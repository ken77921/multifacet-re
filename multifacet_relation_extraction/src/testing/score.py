import argparse
import os
import numpy as np
import random
import torch
import pandas as pd
import pickle
import logging
import sys

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

sys.path.insert(0, sys.path[0]+'/..')
from utils.utils import seed_all_randomness, load_corpus, loading_all_models, str2bool, F2SetDataset
from utils.utils_testing import predict_batch_simple, lc_pred_dist, compute_cosine_sim, max_cosine_given_sim, add_model_arguments

parser = argparse.ArgumentParser(description='PyTorch Neural Set Decoder for Sentnece Embedding')

###path
parser.add_argument('--data', type=str, default='./data/correct_preprocessed/',
                    help='location of the data corpus')
parser.add_argument('--candidate_file', type=str, default="data/candidates/full_sentence_candidates_2012",
                    help='location of the candidate file')
# parser.add_argument('--entpair_vocab_map', type=str, default='./data/correct_preprocessed/',
#                     help='location of the mapping from short entpair vocab to actual entpairs')
parser.add_argument('--checkpoint', type=str, default='./models/',
                    help='model checkpoint to use')
parser.add_argument('--outf', type=str, default='output/scored_candidate_file.txt',
                    help='output file for generated text')

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

### eval params
parser.add_argument('--spanish', default=False, action='store_true',
                    help='evaluating spanish data')
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

# Set the random seed manually for reproducibility.
seed_all_randomness(args.seed,args.cuda,randomness=args.randomness)

########################
print("Loading data")
########################
device = torch.device("cuda" if args.cuda else "cpu")

idx2word_freq, target_idx2word_freq, dataloader_train_arr, dataloader_val, dataloader_val_shuffled, max_sent_len = load_corpus(args.data, args.batch_size, args.batch_size, device, skip_training = True, want_to_shuffle_val = False)
dataloader_train = dataloader_train_arr[0]

# entpair_vocab_map = {}
# with open(args.entpair_vocab_map, "r") as fin:    
#     for line in fin:
#         line = line.rstrip()
#         index = line.find(":")
#         entpair_vocab_map[line[:index]] = line[index+1:]
pattern_vocab = {word[0] : index for index, word in enumerate(idx2word_freq)}
unk_idx = pattern_vocab['<unk>']
eos_idx = pattern_vocab['<eos>']
es_dict = {}
if args.spanish:
    with open("resources/en_es.dictionary.uniq", "r") as fin:
        for line in fin:
            parts = line.strip().split()
            es_dict[parts[1]] = parts[0]

########################
print("Loading Models")
########################
parallel_encoder, parallel_decoder, encoder, decoder, word_norm_emb, target_norm_emb = loading_all_models(args, idx2word_freq, target_idx2word_freq, device, max_sent_len)

# tensor data type
store_type = torch.int64
# field names in candidate file


def get_pattern(sent):
    s, e = sent.index('$ARG'), sent.rindex('$ARG')
    assert sent[s+4] != sent[e+4], "Arguments are the same. Check data."
    pattern = sent[s : e+5]
    return pattern 

def pattern2idx(pattern):
    pidx = []
    for token in pattern.strip().split():
        pidx.append(pattern_vocab.get(token.strip(), unk_idx))    
    pidx.append(eos_idx)
    return pidx

def translate_and_get_pattern(sent, start1, end1, start2, end2):
    words = sent.split(' ')
    if start1 < start2:
        words = ['$ARG1'] + words[end1: start2] + ['$ARG2']
    else:
        words = ['$ARG2'] + words[end2: start1] + ['$ARG1']
    translated = ' '.join([es_dict.get(word, word) for word in words])
    return translated

def process_file(candidate_file):
    data = []    
    field_names = ['Query Id', 'Relation', 'Relation Index', 'Slot Filler', 'Doc Id', 'Start1', 'End1', 'Start2', 'End2', 'Sentence','Pattern', 'Pattern Index']
    with open(candidate_file, 'r') as fin:        
        for line in fin:
            fields = line.strip().split('\t')
            qid, rel, qarg, docid, start1, end1, start2, end2, sent = [field for field in fields]            

            if args.spanish:
                pattern = translate_and_get_pattern(sent, int(start1), int(end1), int(start2), int(end2))
            else:
                # keep only part between $ARG1 and $ARG2
                pattern = get_pattern(sent)
            # convert this part (pattern) to indices
            pattern_idx = pattern2idx(pattern)
            fields.append(pattern) 
            fields.append(pattern_idx) 
            
            # convert kb relation to index
            rel_idx = pattern2idx(rel)
            assert len(rel_idx) == 2 and rel_idx[-1] == eos_idx, 'Relation {} does not have length 1 without eos'.format(rel)
            fields.insert(2, rel_idx)

            data.append(fields)
        
    candidates = pd.DataFrame(data, columns=field_names)
    print(candidates)

    rel_indices = candidates['Relation Index']
    pattern_indices = candidates['Pattern Index']

    # print(rel_indices)
    with torch.no_grad():
        rel_tensor, rel_set_tensor = to_rel_tensor(rel_indices)
        pattern_tensor, pattern_lens, ignored = to_pattern_tensor(pattern_indices)
        valid_ind = torch.from_numpy(np.setxor1d(np.arange(rel_tensor.size(0)), ignored).astype(np.int))
        rel_tensor = rel_tensor[valid_ind]

    return candidates, pattern_tensor, pattern_lens, ignored, rel_tensor, rel_set_tensor

def to_rel_tensor(rels):
    rel_set = set(tuple(rel) for rel in rels)
    rel_set_tensor = torch.zeros(len(rel_set), 2, dtype=store_type, device=device)
    rel_idx_map = {}
    for i, rel in enumerate(rel_set):
        rel_set_tensor[i] = torch.tensor(rel, dtype=store_type, device=device)
        rel_idx_map[rel[0]] = i

    rel_tensor = torch.zeros(len(rels), 1, dtype=store_type, device=device)
    for i, rel in enumerate(rels):                
        rel_tensor[i] = torch.tensor(rel_idx_map[rel[0]], dtype=store_type, device=device)
    

    print("{} relations ready to be tested.".format(len(rel_set)))
    return rel_tensor, rel_set_tensor 


def to_pattern_tensor(patterns):
    ignore = sum([len(pattern) > max_sent_len for pattern in patterns])    
    N = len(patterns) - ignore

    pattern_tensor = torch.zeros(N, max_sent_len, dtype=store_type, device=device)
    pattern_lens = torch.zeros(N, 1, dtype=store_type, device=device)

    ignored = []
    i = 0
    for j, pattern in enumerate(patterns):
        pattern_len = len(pattern)
        if pattern_len <= max_sent_len:
            pattern_tensor[i, -pattern_len:] = torch.tensor(pattern, dtype=store_type, device=device)
            pattern_lens[i] = pattern_len
            i += 1            
        else:
            ignored.append(j)

    print("{} patterns ignored as they exceed max len".format(ignore))
    print("{} patterns ready to be tested.".format(N))
    return pattern_tensor, pattern_lens, ignored


def score(pattern_tensor, pattern_lens, rel_tensor, rel_set_tensor, scorers):
    encoder.eval()
    decoder.eval()
    parallel_encoder.eval()    
    parallel_decoder.eval()

    max_basis = max(args.n_basis_kb, args.n_basis)

    with torch.no_grad():   
        _, rel_basis_pred, rel_output_emb_last, rel_output_emb = predict_batch_simple(rel_set_tensor, parallel_encoder, parallel_decoder, normalize=False)
        rel_mask = (torch.arange(max_basis) < args.n_basis_kb).to(dtype=rel_basis_pred.dtype, device=rel_basis_pred.device).view(1, -1, 1).expand(rel_basis_pred.shape)
        rel_basis_pred = rel_basis_pred * rel_mask

        avg_rel_output_emb = torch.mean(rel_output_emb, dim=1, keepdim=True)
        rel_output_emb_norm = avg_rel_output_emb / (1e-12 + avg_rel_output_emb.norm(dim=2, keepdim=True))
        rel_basis_pred_norm = rel_basis_pred / (1e-12 + rel_basis_pred.norm(dim=2, keepdim=True))

    use_cuda = (device.type == 'cuda')
    batch_size = args.batch_size
    loader = torch.utils.data.DataLoader(F2SetDataset(pattern_tensor, None, None, None, device), \
        batch_size=batch_size, shuffle=False, pin_memory=not use_cuda, drop_last=False)        
    
    scores = {scorer:[] for scorer in scorers}

    for batch_num, batch in enumerate(loader):        
        with torch.no_grad():
            _, pattern_basis_pred_for_batch, _, pattern_output_emb_for_batch = predict_batch_simple(batch[0], parallel_encoder, parallel_decoder, normalize=False)

            pat_mask = (torch.arange(max_basis) < args.n_basis).to(dtype=pattern_basis_pred_for_batch.dtype, device=pattern_basis_pred_for_batch.device).view(1, -1, 1).expand(pattern_basis_pred_for_batch.shape)
            pattern_basis_pred_for_batch = pattern_basis_pred_for_batch * pat_mask

            batch_len, seq_len, _ = pattern_output_emb_for_batch.shape
            select_indices = batch_num*batch_size + torch.arange(batch_len)            

            mask = ~(torch.arange(seq_len).expand(batch_len, seq_len).to(device) < (seq_len - pattern_lens[select_indices])).unsqueeze(-1)
            pattern_output_emb_for_batch = pattern_output_emb_for_batch.masked_fill(mask, 0)
            avg_pattern_output_emb_for_batch = torch.sum(pattern_output_emb_for_batch, dim=1) / pattern_lens[select_indices].to(torch.float) 
            avg_pattern_output_emb_for_batch = avg_pattern_output_emb_for_batch.unsqueeze(1)
            avg_pattern_output_emb_for_batch_norm = avg_pattern_output_emb_for_batch / (1e-12 + avg_pattern_output_emb_for_batch.norm(dim=2, keepdim=True))        
            pattern_basis_pred_for_batch_norm = pattern_basis_pred_for_batch / (1e-12 + pattern_basis_pred_for_batch.norm(dim=2, keepdim=True))            

            select_rel = rel_tensor[select_indices].squeeze(-1)                        
            rel_output_emb_for_batch_norm = rel_output_emb_norm[select_rel]
            rel_basis_pred_for_batch_norm = rel_basis_pred_norm[select_rel]
            
            
            # cos similarity
            cos_scores_r2p, cos_scores_p2r = compute_cosine_sim(rel_output_emb_for_batch_norm, avg_pattern_output_emb_for_batch_norm)
            # cos similarity - basis
            cos_scores_basis_r2p, cos_scores_basis_p2r = compute_cosine_sim(rel_basis_pred_for_batch_norm, pattern_basis_pred_for_batch_norm)
            # max cos r2p
            max_cos_scores_r2p = max_cosine_given_sim(cos_scores_basis_r2p)
            # max cos p2r
            max_cos_scores_p2r = max_cosine_given_sim(cos_scores_basis_p2r)
            # max cos avg
            max_cos_scores_avg = (max_cos_scores_r2p + max_cos_scores_p2r)/2
            # lcd r2p
            lcd_r2p_scores = lc_pred_dist(pattern_basis_pred_for_batch_norm, rel_basis_pred_for_batch_norm, None, args.L1_losss_B, device)            
            # lcd p2r
            lcd_p2r_scores = lc_pred_dist(rel_basis_pred_for_batch_norm, pattern_basis_pred_for_batch_norm, None, args.L1_losss_B, device)
            # lcd avg
            lcd_avg_scores = (lcd_r2p_scores + lcd_p2r_scores)/2
        
        scores['cos'].extend(cos_scores_p2r.squeeze(-1).cpu())
        scores['max_cos_p2r'].extend(max_cos_scores_p2r.squeeze(-1).cpu()) 
        scores['max_cos_r2p'].extend(max_cos_scores_r2p.squeeze(-1).cpu()) 
        scores['max_cos_avg'].extend(max_cos_scores_avg.squeeze(-1).cpu()) 
        scores['lcd_r2p'].extend((1-lcd_r2p_scores).squeeze(-1).cpu()) 
        scores['lcd_p2r'].extend((1-lcd_p2r_scores).squeeze(-1).cpu()) 
        scores['lcd_avg'].extend((1-lcd_avg_scores).squeeze(-1).cpu())

    return scores
    
################################
# Scoring the candidate file
################################
candidate_file = args.candidate_file
candidates, pattern_tensor, pattern_lens, ignored, rel_tensor, rel_set_tensor = process_file(candidate_file)

# all 7 scores are computed - no facility for options
scorers = ['cos', 'max_cos_r2p', 'max_cos_p2r', 'max_cos_avg', 'lcd_r2p', 'lcd_p2r', 'lcd_avg']
scores = score(pattern_tensor, pattern_lens, rel_tensor, rel_set_tensor, scorers)

# Setting score of 0.0 for lines that were ignored bec pattern was too long
for scorer in scorers:
    all_scores_len = len(scores[scorer]) + len(ignored)
    all_scores = np.zeros(all_scores_len) #if 'lcd' not in scorer else np.ones(all_scores_len)
    valid_ind = np.setxor1d(np.arange(all_scores_len), ignored).astype(np.int)
    all_scores[valid_ind] = [score.item() for score in scores[scorer]]
    candidates[scorer] = all_scores

# Save the scored candidate file
with open(args.outf, 'w') as fout:
    field_names = ['Query Id', 'Relation', 'Slot Filler', 'Doc Id', 'Start1', 'End1', 'Start2', 'End2', 'Sentence'] + scorers
    candidates.to_csv(fout, index=False, sep='\t', header=False, columns=field_names)

    
