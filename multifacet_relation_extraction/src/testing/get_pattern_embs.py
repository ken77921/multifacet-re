import argparse
import os
import torch
import pickle
import logging
from collections import defaultdict
from tqdm import tqdm
import warnings

warnings.simplefilter("ignore")

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s: %(message)s')
log = logging.getLogger('get_patterns')

import sys
sys.path.insert(0, sys.path[0]+'/..')
from utils.utils import seed_all_randomness, load_corpus, loading_all_models, str2bool
from utils.utils_testing import predict_batch_simple, add_model_arguments

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
parser.add_argument('--outdir', type=str, default='output/patterns/',
                    help='output dir for sentence pattern embs and basis preds')

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
data_arr = [*dataloader_train_arr, dataloader_val_shuffled]

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

log.info("Save dir: {}".format(args.outdir))

########################
log.info("Obtaining basis preds")
########################
with torch.no_grad(), open(os.path.join(args.outdir, "all_data.txt"), 'w') as fout:
    # All sentence patterns of train set
    patterns = []
    # pattern index to no. of bases mapping
    patidx2num_basis = defaultdict(int)
    patidx2targets = defaultdict(list)
    for i, dataloader_train in enumerate(data_arr):
        for batch in tqdm(dataloader_train):
            #batch = next(iter(dataloader_train))
            feature, target, kb_marker, num_basis = batch 
            
            # indices of patterns
            pat_indices = (kb_marker == 0).nonzero().flatten()
            # (N, L) --> K = no. of patterns in batch
            pat_features = feature[pat_indices]                                   
            pat_tuples = [tuple(f) for f in pat_features.tolist()]
            patterns.extend(pat_tuples)
            for j, pat_idx in enumerate(pat_indices):
                fidx = pat_tuples[j]
                patidx2num_basis[fidx] = num_basis[pat_idx].item()+1 if num_basis is not None and len(num_basis) > 0 else args.n_basis                
                patidx2targets[fidx].append(target[pat_idx])
                assert len(target[pat_idx]) == 5, "Target length is not 5!"

    patterns = torch.unique(torch.tensor(patterns, device=device, dtype=torch.long), dim=0, sorted=False)
    print(patterns)

    print("Finished reading all sentence patterns. patterns: {}".format(patterns.shape))
    
    pat_basis_preds = []
    idx2pat = {}
    indices = []
    pat_num_basis = []
    for i, pat in tqdm(enumerate(patterns), total=len(patterns)):
        pat_idx = tuple(pat.tolist())
        t = torch.cat(patidx2targets[pat_idx])
        shape_before = t.shape
        t = t[t != 0].tolist()
        shape_after = len(t)
        if len(t) >= 1:
            indices.append(i)
            pat_num_basis.append(patidx2num_basis[pat_idx])
            idx2pat[pat_idx] = ' '.join([idx2word[idx] for idx in pat[pat != 0].tolist()])            
            patidx2targets[pat_idx] = [entpair_vocab_map["ep{}".format(epidx)] for epidx in t]
            fout.write("{}\n{}\n\n".format(idx2pat[pat_idx], patidx2targets[pat_idx]))
        else:
            patidx2targets.pop(pat_idx)
        #print('{}'.format(idx2pat[pat_idx]))
    pat_num_basis = torch.tensor(pat_num_basis, device=device, dtype=torch.long)        
    patterns = patterns[torch.tensor(indices, device=device)]
    print('pat_num_basis:', pat_num_basis.shape, 'patterns:', patterns.shape)

    log.info("Running the sentence patterns through the model.")
    zero_count = 0
    before_mask = 0
    
    for start in tqdm(range(0, len(patterns), args.batch_size)):
        pattern_batch = patterns[start: start + args.batch_size]
        pat_num_basis_batch = pat_num_basis[start: start + args.batch_size]
        # Obtain basis pred and emb for patterns
        coeff_pred, pat_basis_pred, pat_output_emb_last, pat_output_emb = predict_batch_simple(pattern_batch, parallel_encoder, parallel_decoder, normalize=False)
        
        if torch.allclose(pat_basis_pred, torch.zeros_like(pat_basis_pred)):
            before_mask += len(pattern_batch)
        pat_num_basis_batch = pat_num_basis_batch.clamp(max=args.n_basis)        
        max_basis = max(args.n_basis, args.n_basis_kb)
        # Create the mask: (N, T)
        pat_mask = (torch.arange(max_basis).expand(pattern_batch.shape[0], -1) \
                    .to(dtype=pat_num_basis.dtype, device=pat_num_basis.device) \
                    < pat_num_basis_batch.view(-1, 1)).to(dtype=pat_num_basis.dtype, device=pat_num_basis.device)
        # print(pat_mask)
        pat_mask = pat_mask.unsqueeze(-1)

        pat_basis_pred = pat_basis_pred * pat_mask        
        pat_basis_pred_norm = pat_basis_pred/(1e-12 + pat_basis_pred.norm(dim=2, keepdim=True))
        pat_output_emb_norm = pat_output_emb/(1e-12 + pat_output_emb.norm(dim=2, keepdim=True))
        if torch.allclose(pat_basis_pred_norm, torch.zeros_like(pat_basis_pred_norm)):
            zero_count += len(pattern_batch)
        pat_basis_preds.append(pat_basis_pred_norm.detach().cpu())
    print("Zeros:- before mask:{}, after mask:{}".format(before_mask, zero_count))
        
# # Save the numpy arrays and the dictionary
# np.save(os.path.join(args.outdir, "basis_pred.npy"), kb_rel_basis_pred_np)
# np.save(os.path.join(args.outdir, "emb.npy"), kb_rel_output_emb_np)
torch.save(torch.cat(pat_basis_preds, dim=0), os.path.join(args.outdir, "pat_basis_pred.pt"))

    
with open(os.path.join(args.outdir, "idx2pat_dict.pkl"), 'wb') as fout:
    pickle.dump(idx2pat, fout, protocol=pickle.HIGHEST_PROTOCOL)
with open(os.path.join(args.outdir, "idx2ep_dict.pkl"), 'wb') as fout:
    pickle.dump(patidx2targets, fout, protocol=pickle.HIGHEST_PROTOCOL)
with open(os.path.join(args.outdir, "pattern_list.txt"), "w") as fout:
    for pat in list(idx2pat.values()):
        fout.write("{}\n".format(pat))
log.info("Save Complete!")