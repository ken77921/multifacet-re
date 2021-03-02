import pickle
import torch
import numpy as np
import os
import pandas as pd
import sys
sys.path.insert(0, '/mnt/nfs/scratch1/rohpaul/akbc/multifacet-emb-relation-extraction/NSD_for_sentence_embedding/src')
from utils_testing import lc_pred_dist, compute_cosine_sim, max_cosine_given_sim
from tqdm import tqdm
import argparse
import re
from sklearn.metrics import average_precision_score

parser = argparse.ArgumentParser(description="Finding entailment scores for specific-general pattern pairs produced by WordNet")
parser.add_argument('--emb_dir', type=str, default='output/milestone_run_trans-b5-kb11',
                    help='folder of embeddings produced by model on train set')
parser.add_argument('--wordnet_patterns', type=str, default='../dataset/RE_entailment_labels_test.tsv',
                    help='file name for wordnet patterns for which we wish to compute entailment scores')
parser.add_argument('--pat_emb', type=str, default='./data/CUSchema_scored_candidates',
                    help='The embedding from Pat LSTM baseline model')
parser.add_argument('--save', type=str,  default='entailment_scores.txt',
                    help='file name where we wish to store the nearest neighbors')
parser.add_argument('--L1_loss_B', type=float, default=0.2,
                    help='L1 loss coefficient')
parser.add_argument('--batch_size', type=int, default=100,
                    help='batch size for computing scores')
parser.add_argument('--max_sent_len', type=int, default=20,
                    help='max length for each pattern, the wordnet patterns do not satisfy the length constraint, so this param is needed')

args = parser.parse_args();

# Device to use (always use cuda if available)
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print("Using", DEVICE)

L1_loss_B = args.L1_loss_B


OUTDIR = args.emb_dir
PAT_DIR = "patterns"
BASIS_PRED_FILE = "basis_pred.npy"
PAT_BASIS_PRED_FILE = "pat_basis_pred.pt"
EMB_FILE = "emb.npy"
IDX2PAT_FILE = "idx2pat_dict.pkl"
IDX2EP_FILE = "idx2ep_dict.pkl"
# FREEBASE_MAP = "data/en-freebase_wiki_cat_title_map.txt"
#SAVE_FILE = os.path.join(OUTDIR, PAT_DIR, args.save)
SAVE_FILE = os.path.join(args.save)
INPUT_PATTERNS_FILE = os.path.join(args.wordnet_patterns)

# Load patterns produced by model
patterns=torch.load(os.path.join(OUTDIR, PAT_DIR, PAT_BASIS_PRED_FILE), map_location=DEVICE)
with open(os.path.join(OUTDIR, PAT_DIR, IDX2PAT_FILE), 'rb') as fin:
    idx2pat = pickle.load(fin)
# Load entity pairs that co-occur with the training patterns
with open(os.path.join(OUTDIR, PAT_DIR, IDX2EP_FILE), 'rb') as fin:
    idx2ep = pickle.load(fin)

pat2idx = {pat:i for i, pat in enumerate(idx2pat.values())}
pat_texts = list(idx2pat.values())

pattern_d2_LSTM_emb = {}
with open(args.pat_emb) as f_in:
    for line in f_in:
        pattern, emb_str = line.rstrip().split('\t')
        pattern_d2_LSTM_emb[pattern] = np.array([float(x) for x in emb_str.split(' ')])

# # Load freebase map mapping codes to freebase entities
# freebase_map = {}
# with open(FREEBASE_MAP, 'r') as fin:
#     for line in fin:
#         parts = line.strip().split('\t')
#         freebase_map[parts[1]] = parts[0]        
#         assert len(parts) == 2, "Got length: {}".format(len(parts))

#         eps = [idx2ep[pat_idx] for pat_idx in idx2pat]

# # Util functions for code to entity conversion
# def convert_fbentity(e):
#     if e in freebase_map:
#         return freebase_map[e]
#     return e

# def convert(eplist):
#     return ['\t'.join(list(map(convert_fbentity, ep.split('\t')))) for ep in eplist]

# Compute entailment scores for a source pattern against targets provided
def get_pat_entailment_scores_single_source_single_target(source, target):
    specific_basis_pred = source
    general_basis_pred = target
    
    print(specific_basis_pred.shape, general_basis_pred.shape)
    # kmeans sim scores
    cos_scores_basis_s2g, cos_scores_basis_g2s = compute_cosine_sim(specific_basis_pred, general_basis_pred)
    # kmeans: specific --> general
    max_cos_scores_s2g = max_cosine_given_sim(cos_scores_basis_s2g)
    # kmeans: general --> specific
    max_cos_scores_g2s = max_cosine_given_sim(cos_scores_basis_g2s)
    # kmeans: avg
    max_cos_scores_avg = (max_cos_scores_s2g + max_cos_scores_g2s)/2
    max_cos_scores_diff = (max_cos_scores_s2g - max_cos_scores_g2s)
    # kmeans: entailment score
    #kmeans_entail = (max_cos_scores_g2s - max_cos_scores_s2g) * max_cos_scores_avg
    # kmeans: sign and direction aligned
    #kmeans_sign = (max_cos_scores_g2s > max_cos_scores_s2g) * max_cos_scores_avg
    # sc dist scores
    # sc: specific --> general
    #lcd_s2g_scores = lc_pred_dist(general_basis_pred, specific_basis_pred, None, L1_loss_B, DEVICE)            
    # sc: general --> specific
    #lcd_g2s_scores = lc_pred_dist(specific_basis_pred, general_basis_pred, None, L1_loss_B, DEVICE)
    # sc: avg
    #lcd_avg_scores = (lcd_s2g_scores + lcd_g2s_scores)/2
    # sc: entailment score
    #lcd_entail = (lcd_g2s_scores - lcd_s2g_scores) * lcd_avg_scores
    # sc: sign and dir aligned
    #lcd_sign = (lcd_g2s_scores > lcd_s2g_scores) * lcd_avg_scores
        
    scores = torch.cat([max_cos_scores_s2g.view(-1, 1), \
                        max_cos_scores_g2s.view(-1, 1), \
                        max_cos_scores_avg.view(-1, 1), \
                        max_cos_scores_diff.view(-1, 1)], \
                        #kmeans_entail.view(-1, 1), \
                        #kmeans_sign.view(-1, 1), \
                        #lcd_s2g_scores.view(-1, 1), \
                        #lcd_g2s_scores.view(-1, 1), \
                        #lcd_avg_scores.view(-1, 1), \
                        #lcd_entail.view(-1, 1), \
                        #lcd_sign.view(-1, 1)], \
                        dim=1)
       
    return scores

def update_direction_acc(direction_correct, diff, label):
    if (label == '>' and diff > 0) or (label == '<' and diff < 0):
        direction_correct.append(1)
    elif diff == 0 and (label == '>' or label == '<'):
        direction_correct.append(0.5)
    elif (label == '>' or label == '<'):
        direction_correct.append(0)

def update_direction_acc_category(direction_all, direction_n, direction_v, diff, label, pos_tag):
    update_direction_acc(direction_all, diff, label)
    if pos_tag == 'v': 
        update_direction_acc(direction_v, diff, label)
    if pos_tag == 'n': 
        update_direction_acc(direction_n, diff, label)

# Finds the entailment scores
def get_pattern_entailment_scores(spec_gen_list, all_patterns, pat2idx, pat_texts, outf):   
    score_names = ["kmeans_s2g", "kmeans_g2s", "kmeans_avg", "kmeans_diff"]
    output_list = []
    direction_arr = {}
    direction_all = []
    direction_n = []
    direction_v = []
    direction_baseline_arr = {}
    direction_baseline_all = []
    direction_baseline_n = []
    direction_baseline_v = []
    y_gt = []
    y_pred = []
    y_pred_all = []
    y_pred_abs_all = []
    y_pred_sim_no_N = []
    y_LSTM_sim_no_N = []
    y_baseline = []
    y_gt_ent_sim = []
    y_gt_eq_sim = []
    y_gt_eq_ent_sim = []
    y_pred_sim = []
    y_pred_s2g = []
    y_pred_g2s = []
    y_baseline_sim = []
    y_baseline_abs_sim = []
    y_LSTM_sim = []
    for start in range(0, len(spec_gen_list), args.batch_size):
        batch = spec_gen_list[start: start + args.batch_size]
        
        batch_indices = torch.tensor([[pat2idx[spec], pat2idx[gen]] for label, pos_tag, spec, gen, spec_freq, gen_freq in batch], dtype=torch.long, device=DEVICE)
        scores = get_pat_entailment_scores_single_source_single_target(all_patterns[batch_indices[:, 0]], all_patterns[batch_indices[:, 1]])
        #scores = get_pat_entailment_scores_single_source_single_target(all_patterns[batch_indices[:, 0]], all_patterns[batch_indices[:, 0]])
        for i, (label, pos_tag, spec, gen, spec_freq, gen_freq) in enumerate(batch):
            extra_word = []
            for w in gen.split()[1:-1]:
                if w not in spec:
                    extra_word.append(w)

            s2g, g2s, avg, diff = scores[i]
            #outf.write('{}\t{}\t{}\t{}\t{}\t{}\t\n'.format(spec, gen, s2g, g2s, avg, diff))
            diff_baseline = (int(gen_freq) - int(spec_freq))/ float(max(int(gen_freq), int(spec_freq)))
            if label != 'N' and label != ':':
                extra_word_key = tuple(extra_word)
                if extra_word_key not in direction_arr:
                    direction_arr[extra_word_key] = []
                if extra_word_key not in direction_baseline_arr:
                    direction_baseline_arr[extra_word_key] = []
                update_direction_acc(direction_arr[extra_word_key], diff, label)
                update_direction_acc(direction_baseline_arr[extra_word_key], diff_baseline, label)
                update_direction_acc_category(direction_all, direction_n, direction_v, diff, label, pos_tag)
                update_direction_acc_category(direction_baseline_all, direction_baseline_n, direction_baseline_v, diff_baseline, label, pos_tag)
            y_pred_sim.append(avg)
            y_pred_abs_all.append( abs(diff.item()) )
            y_baseline_abs_sim.append( abs(diff_baseline) )
            if label == '<':
                y_pred_s2g.append(g2s)
                y_pred_g2s.append(s2g)
                y_pred_all.append(-diff.item())
                y_baseline_sim.append(-diff_baseline)
            else:
                y_pred_s2g.append(s2g)
                y_pred_g2s.append(g2s)
                y_pred_all.append(diff.item())
                y_baseline_sim.append(diff_baseline)

                #y_pred_all.append(abs(diff.item()))
                #y_baseline_sim.append(-abs(diff_baseline))

            s_emb = pattern_d2_LSTM_emb[spec.replace(' <eos>','')]
            g_emb = pattern_d2_LSTM_emb[gen.replace(' <eos>','')]
            LSTM_sim = np.dot(s_emb, g_emb) / ( np.linalg.norm(s_emb) * np.linalg.norm(g_emb))
            y_LSTM_sim.append(LSTM_sim)
            output_list.append([label, pos_tag, spec, gen, s2g, g2s, avg, diff_baseline, diff, LSTM_sim])
            if label == 'N':
                y_gt_eq_sim.append(0)
                y_gt_eq_ent_sim.append(0)
                y_gt_ent_sim.append(0)
            elif label == ':':
                y_gt_eq_sim.append(1)
                y_gt_eq_ent_sim.append(1)
                y_gt_ent_sim.append(0)
            else:
                y_gt_eq_sim.append(0)
                y_gt_eq_ent_sim.append(1)
                y_gt_ent_sim.append(1)

            if label != 'N':
                if label == ':':
                    y_gt.append(0)
                else:
                    y_gt.append(1)
                y_pred.append(abs(diff.item()))
                y_pred_sim_no_N.append(-avg)
                y_LSTM_sim_no_N.append(-LSTM_sim)
                y_baseline.append(abs(diff_baseline))
                #if label == '<':
                #    y_pred.append(-diff.item())
                #    y_baseline.append(-diff_baseline)
                #else:
                #    y_pred.append(diff.item())
                #    y_baseline.append(diff_baseline)
            #outf.write('[{}] ==> [{}]\n'.format(spec, gen))
            #outf.write('\n'.join(["\t{}: {:.4f}".format(score_name, score) for score_name, score in zip(score_names, scores[i])]))
            #outf.write('\n')
        #outf.write('\n')
    output_list_sorted = sorted(output_list, key = lambda x: x[4], reverse=True)
    for label, pos_tag, spec, gen, s2g, g2s, avg, diff_baseline, diff, LSTM_sim in output_list_sorted:
        outf.write('{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(label, pos_tag, spec, gen, s2g, g2s, avg, diff_baseline, diff, LSTM_sim))
    outf.write("directional accuracy: {}\n".format(np.mean(direction_all)))
    outf.write("directional noun accuracy: {}\n".format(np.mean(direction_n)))
    outf.write("directional verb accuracy: {}\n".format(np.mean(direction_v)))
    outf.write("AP entailment from =: {}\n".format(average_precision_score(y_gt, y_pred)))
    outf.write("AP entailment from = sim: {}\n".format(average_precision_score(y_gt, y_pred_sim_no_N)))
    outf.write("AP = from all: {}\n".format(average_precision_score(y_gt_eq_sim, y_pred_sim)))
    outf.write("AP entailment = from all: {}\n".format(average_precision_score(y_gt_eq_ent_sim, y_pred_sim)))
    outf.write("AP entailment from all sim_avg: {}\n".format(average_precision_score(y_gt_ent_sim, y_pred_sim)))
    outf.write("AP entailment from all diff: {}\n".format(average_precision_score(y_gt_ent_sim, y_pred_all)))
    outf.write("AP entailment from all abs diff: {}\n".format(average_precision_score(y_gt_ent_sim, y_pred_abs_all)))
    outf.write("AP entailment from all s2g: {}\n".format(average_precision_score(y_gt_ent_sim, y_pred_s2g)))
    outf.write("AP entailment from all g2s: {}\n".format(average_precision_score(y_gt_ent_sim, y_pred_g2s)))
    direction_avg = []
    for extra_word_key in direction_arr:
        avg_acc = np.mean(direction_arr[extra_word_key])
        outf.write("{}\t{}\t{}".format(extra_word_key, avg_acc, len(direction_arr[extra_word_key])))
        direction_avg.append(avg_acc)
    outf.write("directional pooling accuracy: {}\n".format(np.mean(direction_avg)))

    outf.write("directional baseline accuracy: {}\n".format(np.mean(direction_baseline_all)))
    outf.write("directional baseline noun accuracy: {}\n".format(np.mean(direction_baseline_n)))
    outf.write("directional baseline verb accuracy: {}\n".format(np.mean(direction_baseline_v)))
    outf.write("AP baseline entailment from =: {}\n".format(average_precision_score(y_gt, y_baseline)))
    outf.write("AP baseline = from all: {}\n".format(average_precision_score(y_gt_eq_sim, y_baseline_sim)))
    outf.write("AP baseline entailment = from all: {}\n".format(average_precision_score(y_gt_eq_ent_sim, y_baseline_sim)))
    outf.write("AP baseline entailment from all: {}\n".format(average_precision_score(y_gt_ent_sim, y_baseline_sim)))
    outf.write("AP baseline abs entailment from all: {}\n".format(average_precision_score(y_gt_ent_sim, y_baseline_abs_sim)))
    direction_avg = []
    for extra_word_key in direction_baseline_arr:
        avg_acc = np.mean(direction_baseline_arr[extra_word_key])
        outf.write("{}\t{}\t{}".format(extra_word_key, avg_acc, len(direction_baseline_arr[extra_word_key])))
        direction_avg.append(avg_acc)
    outf.write("directional baseline pooling accuracy: {}\n".format(np.mean(direction_avg)))
    
    outf.write("AP LSTM entailment from = sim: {}\n".format(average_precision_score(y_gt, y_LSTM_sim_no_N)))
    outf.write("AP LSTM = from all: {}\n".format(average_precision_score(y_gt_eq_sim, y_LSTM_sim)))
    outf.write("AP LSTM entailment = from all: {}\n".format(average_precision_score(y_gt_eq_ent_sim, y_LSTM_sim)))
    outf.write("AP LSTM entailment from all: {}\n".format(average_precision_score(y_gt_ent_sim, y_LSTM_sim)))

spec_gen_list = []
with open(INPUT_PATTERNS_FILE, 'r') as fin:
    #top_k = 200
    top_k = 10000
    for count, line in enumerate(fin):
        parts = line.strip().split('\t')
        parts[2] = re.sub('\s+', ' ', parts[2].replace(u'\xa0', u' ')).strip() + ' <eos>'
        parts[3] = re.sub('\s+', ' ', parts[3].replace(u'\xa0', u' ')).strip() + ' <eos>'
        if len(parts[2].split()) <= args.max_sent_len and len(parts[3].split()) <= args.max_sent_len:
            spec_gen_list.append((parts[0], parts[1], parts[2], parts[3], parts[5], parts[6]))
        if count >= top_k:
            break

print("{} pairs of patterns".format(len(spec_gen_list)))
# Find and save the computed nearest neighbors
with open(SAVE_FILE, 'w') as outf:
    get_pattern_entailment_scores(spec_gen_list, patterns, pat2idx, pat_texts, outf)
