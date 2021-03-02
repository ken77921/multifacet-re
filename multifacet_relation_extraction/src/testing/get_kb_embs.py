
import argparse
import os
import numpy as np
import random
import torch
import pickle
import logging
from collections import defaultdict
from tqdm import tqdm

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s: %(message)s')
log = logging.getLogger('get_kb_rels')

import sys
sys.path.insert(0, sys.path[0]+'/..')
from utils.utils import seed_all_randomness, load_corpus, loading_all_models, str2bool, F2SetDataset, compute_freq_prob_idx2word
from utils.utils_testing import predict_batch_simple, lc_pred_dist, compute_cosine_sim, max_cosine_given_sim, add_model_arguments, print_basis_text

parser = argparse.ArgumentParser(description='PyTorch Neural Set Decoder for Sentnece Embedding')

###path
parser.add_argument('--data', type=str, default='./data/correct_preprocessed/',
                    help='location of the data corpus')
# parser.add_argument('--candidate_file', type=str, default="data/candidates/full_sentence_candidates_2012",
#                     help='location of the candidate file')
# parser.add_argument('--entpair_vocab_map', type=str, default='./data/correct_preprocessed/',
#                     help='location of the mapping from short entpair vocab to actual entpairs')
parser.add_argument('--checkpoint', type=str, default='./models/',
                    help='model checkpoint to use')
parser.add_argument('--outdir', type=str, default='output/kb_rels/',
                    help='output dir for kb relation embs and basis preds')

###system
parser.add_argument('--seed', type=int, default=1111,
                    help='random seed')
parser.add_argument('--randomness', type=str2bool, nargs='?', default=True,
                    help='use randomness')
parser.add_argument('--cuda', type=str2bool, nargs='?', default=torch.cuda.is_available(),
                    help='use CUDA')
parser.add_argument('--single_gpu', default=False, action='store_true',
                    help='use single GPU')
parser.add_argument('--batch_size', type=int, default=1, metavar='N',
                    help='batch size')
parser.add_argument('--max_batch_num', type=int, default=100, 
                    help='number of batches for evaluation')
parser.add_argument('--entpair_vocab_map', type=str, default='', 
                    help='location of vocab map')
parser.add_argument('--top_k', type=int, default=5,
                    help='k nearest neighbors')
# parser.add_argument('--rare', default=False, action='store_true',
#                     help='emphasize on rare entity pairs')
# parser.add_argument('--coeff_opt', type=str, default='lc',
#                     help='Could be max, lc, maxlc')
# parser.add_argument('--coeff_opt_algo', type=str, default='rmsprop',
# #parser.add_argument('--coeff_opt_algo', type=str, default='sgd_bmm',
#                     help='Could be sgd_bmm, sgd, asgd, adagrad, rmsprop, and adam')
### eval params
parser.add_argument('--L1_losss_B', type=float, default=0.2,
                    help='L1 loss for the coefficient matrix')

add_model_arguments(parser)

args = parser.parse_args()

if args.source_emb_file == "source_emb.pt":
    args.source_emb_file =  os.path.join(args.checkpoint,"source_emb.pt")
if args.target_emb_file == "target_emb.pt":
    args.target_emb_file =  os.path.join(args.checkpoint,"target_emb.pt")
if args.n_basis_kb < 0:
    args.n_basis_kb = args.n_basis

if not os.path.exists(args.outdir):
    os.makedirs(args.outdir)

# Set the random seed manually for reproducibility.
seed_all_randomness(args.seed,args.cuda,randomness=args.randomness)

########################
log.info("Loading data")
########################
device = torch.device("cuda" if args.cuda else "cpu")
# device = torch.device('cpu')

idx2word_freq, target_idx2word_freq, dataloader_train_arr, dataloader_val, dataloader_val_shuffled, max_sent_len = load_corpus(args.data, args.batch_size, args.batch_size, device, skip_training = False, want_to_shuffle_val = False)
dataloader_train = dataloader_train_arr[0]

entpair_vocab_map = {}
with open(args.entpair_vocab_map, "r") as fin:    
    for line in fin:
        line = line.rstrip()
        index = line.find(":")
        entpair_vocab_map[line[:index]] = line[index+1:]
        
pattern_vocab = {word[0] : index for index, word in enumerate(idx2word_freq)}
unk_idx = pattern_vocab['<unk>']
eos_idx = pattern_vocab['<eos>']
idx2word = {v:k for k, v in pattern_vocab.items()}

########################
log.info("Loading Models")
########################
parallel_encoder, parallel_decoder, encoder, decoder, word_norm_emb, target_norm_emb = loading_all_models(args, idx2word_freq, target_idx2word_freq, device, max_sent_len)

with torch.no_grad():
    # All KB relations of train set
    kb_rels = []
    # kb relation index to no. of bases mapping
    kbidx2num_basis = defaultdict(int)
    for i, dataloader_train in enumerate(dataloader_train_arr):
        for batch in tqdm(dataloader_train):
            feature, target, kb_marker, num_basis = batch 
            # indices of kb relations
            kb_indices = (kb_marker == 1).nonzero().flatten()
            # (K, L) --> K = no. of kb relations
            kb_features = feature[kb_indices]
            # kb relations are single-indexed; specifically, they are only the second last
            # index in the feature tensor, everything before are 0s and it is followed by
            # the EOS index
            kb_rels.extend(kb_features[:, -2:].tolist())
            for j, kb_idx in enumerate(kb_indices):
                fidx = kb_features[j, -2].item()
                kbidx2num_basis[fidx] = num_basis[kb_idx].item() if num_basis is not None and len(num_basis) > 0 else args.n_basis_kb

    kb_rels = torch.unique(torch.tensor(kb_rels, device=device, dtype=torch.long), dim=0, sorted=False)
    kb_rels = kb_rels[kb_rels.sum(dim=1) != 0]

    print("Finished reading all KB relations. kb_rels: {}".format(kb_rels.shape))

    idx2kbrel = {}
    kb_num_basis = torch.zeros(kb_rels.shape[0], device=device, dtype=torch.long)
    for i, kb_rel in enumerate(kb_rels[:, 0]):
        kb_rel_idx = kb_rel.item()
        kb_num_basis[i] = kbidx2num_basis[kb_rel_idx]
        idx2kbrel[kb_rel_idx] = idx2word[kb_rel_idx]
        print('{}:\t {}'.format(kb_rel_idx, idx2word[kb_rel_idx]))
    print('kb_num_basis:', kb_num_basis.shape)

    log.info("Running the kb relations through the model.")
    # Obtain basis pred and emb for kb relations
    coeff_pred, kb_rel_basis_pred, kb_rel_output_emb_last, kb_rel_output_emb = predict_batch_simple(kb_rels, parallel_encoder, parallel_decoder, normalize=False)

    kb_num_basis = kb_num_basis.clamp(max=args.n_basis_kb)
    max_basis = max(args.n_basis, args.n_basis_kb)
    # Create the mask: (N, T)
    kb_rel_mask = (torch.arange(max_basis).expand(kb_rels.shape[0], -1).to(dtype=kb_num_basis.dtype, device=kb_num_basis.device)
                   < kb_num_basis.view(-1, 1)).to(dtype=kb_num_basis.dtype, device=kb_num_basis.device)
    kb_rel_mask = kb_rel_mask.unsqueeze(-1)
    print('kb_num_basis clamped:', kb_num_basis.shape)
    print('kb_rel_basis_pred:', kb_rel_basis_pred.shape)
    print('kb_rel_mask:', kb_rel_mask.shape)
    # kb_rel_mask = (torch.arange(kb_rel_basis_pred.shape[1]) < args.n_basis_kb)\
    # .to(dtype=kb_rel_basis_pred.dtype, device=kb_rel_basis_pred.device).view(1, -1, 1).expand(kb_rel_basis_pred.shape)

    kb_rel_basis_pred = kb_rel_basis_pred * kb_rel_mask
    kb_rel_basis_pred_norm = kb_rel_basis_pred/(1e-12 + kb_rel_basis_pred.norm(dim=2, keepdim=True))
    kb_rel_output_emb_norm = kb_rel_output_emb/(1e-12 + kb_rel_output_emb.norm(dim=2, keepdim=True))
        
    coeff_sum = coeff_pred.cpu().detach().numpy()    
    coeff_sum_diff = coeff_pred[:,:,0] - coeff_pred[:,:,1]
    coeff_sum_diff_pos = coeff_sum_diff.clamp(min = 0)
    coeff_sum_diff_cpu = coeff_sum_diff.cpu().detach().numpy()
    coeff_order = np.argsort(coeff_sum_diff_cpu, axis = 1)
    coeff_order = np.flip( coeff_order, axis = 1)

    log.info("Basis preds and relation embs obtained.")
    # Convert basis pred and emb to numpy ndarrays
    kb_rel_basis_pred_np = kb_rel_basis_pred_norm.cpu().detach().numpy()
    kb_rel_output_emb_np = kb_rel_output_emb_norm.cpu().detach().numpy()

    # Find nearest entity pairs for each dimension
    basis_norm_pred = kb_rel_basis_pred_norm.permute(0,2,1)
    top_values = []
    top_indices = []
    for basis_norm_pred_batch in basis_norm_pred:
        sim_pairwise = torch.matmul(target_norm_emb, basis_norm_pred_batch).unsqueeze(0)
        top_value, top_index = torch.topk(sim_pairwise, args.top_k, dim = 1, sorted=True)
        top_values.append(top_value)
        top_indices.append(top_index)
    top_values = torch.cat(top_values, dim=0)
    top_indices = torch.cat(top_indices, dim=0)
    
log.info("Saving in {}".format(args.outdir))

with open(os.path.join(args.outdir, "knn.txt"), "w") as out:
    print_basis_text(kb_rels, idx2word_freq, target_idx2word_freq, entpair_vocab_map, coeff_order, coeff_sum, top_values, top_indices, 0, out, args.n_basis, args.n_basis_kb, torch.ones(kb_rels.shape[0], device=device, dtype=torch.bool))

# Save the numpy arrays and the dictionary
np.save(os.path.join(args.outdir, "basis_pred.npy"), kb_rel_basis_pred_np)
np.save(os.path.join(args.outdir, "emb.npy"), kb_rel_output_emb_np)

with open(os.path.join(args.outdir, "idx2kb_dict.pkl"), 'wb') as fout:
    pickle.dump(idx2kbrel, fout, protocol=pickle.HIGHEST_PROTOCOL)

log.info("Save Complete!")