import argparse
import os
import torch
from tqdm import tqdm
from collections import defaultdict
import sys
sys.path.insert(0, sys.path[0]+'/..')
from utils.utils import seed_all_randomness, load_corpus, loading_all_models, str2bool
from utils import utils_testing
parser = argparse.ArgumentParser(description='PyTorch Neural Set Decoder for Sentnece Embedding')

#path
parser.add_argument('--data', type=str, default='./data/processed/wackypedia/',
                    help='location of the data corpus')
parser.add_argument('--entpair_vocab_map', type=str, default='./data/processed/wackypedia/',
                    help='location of the mapping from short entpair vocab to actual entpairs')
parser.add_argument('--checkpoint', type=str, default='./models/',
                    help='model checkpoint to use')
parser.add_argument('--outf', type=str, default='gen_log/generated.txt',
                    help='output file for generated text')

#system
parser.add_argument('--seed', type=int, default=1111,
                    help='random seed')
parser.add_argument('--randomness', type=str2bool, nargs='?', default=True,
                    help='use randomness')
parser.add_argument('--cuda', type=str2bool, nargs='?', default=True,
                    help='use CUDA')
parser.add_argument('--single_gpu', default=False, action='store_true',
                    help='use single GPU')
parser.add_argument('--batch_size', type=int, default=1, metavar='N',
                    help='batch size')
parser.add_argument('--max_batch_num', type=int, default=100, 
                    help='number of batches for evaluation')
parser.add_argument('--skip_train', default=False, action='store_true',
                    help='Skip visualizing train set')
parser.add_argument('--freq_threshold', type=int, default=5,
                    help='Min. freq of entity pairs to consider')
parser.add_argument('--topk', type=int, default=5,
                    help='topk nearest neighbors to find')

utils_testing.add_model_arguments(parser)

args = parser.parse_args()

if args.source_emb_file == "source_emb.pt":
    args.source_emb_file = os.path.join(args.checkpoint,"source_emb.pt")
if args.target_emb_file == "target_emb.pt":
    args.target_emb_file = os.path.join(args.checkpoint,"target_emb.pt")
if args.n_basis_kb < 0:
    args.n_basis_kb = args.n_basis

# Set the random seed manually for reproducibility.
seed_all_randomness(args.seed,args.cuda, randomness=args.randomness)


########################
print("Loading data")
########################

device = torch.device("cuda" if args.cuda else "cpu")

idx2word_freq, target_idx2word_freq, dataloader_train_arr, dataloader_val, dataloader_val_shuffled, max_sent_len = load_corpus(args.data, args.batch_size, args.batch_size, device, skip_training = args.skip_train, want_to_shuffle_val = False)
dataloader_train = dataloader_train_arr[0]

kb_rels = []
kb_markers = []
kb_num_basis = []
kb_rel_idx = set()
# kb relation index to no. of bases mapping
kbidx2num_basis = defaultdict(int)
for batch in tqdm(dataloader_train):
    feature, target, kb_marker, num_basis = batch
    # indices of kb relations
    kb_indices = (kb_marker == 1).nonzero().flatten()
    # (K, L) --> K = no. of kb relations
    kb_features = feature[kb_indices]
    # kb relations are single-indexed; specifically, they are only the second last
    # index in the feature tensor, everything before are 0s and it is followed by
    # the EOS index
    for j, kb_idx in enumerate(kb_indices):
        fidx = kb_features[j, -2].item()
        if fidx not in kb_rel_idx:
            kb_rel_idx.add(fidx)
            kb_rels.append(kb_features[j].unsqueeze(0))
            if len(kb_marker) != 0:
                kb_markers.append(kb_marker[kb_idx].unsqueeze(0))
            if len(num_basis) != 0:
                kb_num_basis.append(num_basis[kb_idx].unsqueeze(0))

kb_rels = torch.cat(kb_rels, dim=0)
if len(kb_markers) > 0:
    kb_markers = torch.cat(kb_markers, dim=0)
if len(kb_num_basis) > 0:
    kb_num_basis = torch.cat(kb_num_basis, dim=0)

dataloader_train = [(kb_rels[start: start + args.batch_size], None, kb_markers[start: start + args.batch_size], None) for start in range(0, len(kb_rels), args.batch_size)]


entpair_vocab_map = {}
with open(args.entpair_vocab_map, "r") as fin:    
    for line in fin:
        line = line.rstrip()
        index = line.find(":")
        entpair_vocab_map[line[:index]] = line[index+1:]

freebase_map = {}
with open("data/en-freebase_wiki_cat_title_map.txt", 'r') as fin:
    for line in fin:
        parts = line.strip().split('\t')
        freebase_map[parts[1]] = parts[0]
        assert len(parts) == 2, "Got length: {}".format(len(parts))
########################
print("Loading Models")
########################


parallel_encoder, parallel_decoder, encoder, decoder, word_norm_emb, target_norm_emb = loading_all_models(args, idx2word_freq, target_idx2word_freq, device, max_sent_len)

for i, target_freq_idx in enumerate(target_idx2word_freq):
    if target_freq_idx[1] < 5:
        target_norm_emb[i] = 0

encoder.eval()
decoder.eval()

with open(args.outf, 'w') as outf:
    outf.write('Shuffled Validation Topics:\n\n')
    utils_testing.visualize_topics_val(dataloader_val_shuffled, parallel_encoder, parallel_decoder, word_norm_emb, idx2word_freq, target_norm_emb, target_idx2word_freq, entpair_vocab_map, outf, args.n_basis, args.n_basis_kb, args.max_batch_num, freebase_map, args.freq_threshold, args.topk)
    if dataloader_val is not None:
        outf.write('Validation Topics:\n\n')
        utils_testing.visualize_topics_val(dataloader_val, parallel_encoder, parallel_decoder, word_norm_emb, idx2word_freq, target_norm_emb, target_idx2word_freq, entpair_vocab_map, outf, args.n_basis, args.n_basis_kb, args.max_batch_num, freebase_map, args.freq_threshold, args.topk)
    if dataloader_train:
        outf.write('Training Topics:\n\n')
        utils_testing.visualize_topics_val(dataloader_train, parallel_encoder, parallel_decoder, word_norm_emb, idx2word_freq, target_norm_emb, target_idx2word_freq, entpair_vocab_map, outf, args.n_basis, args.n_basis_kb, args.max_batch_num, freebase_map, args.freq_threshold, args.topk)
