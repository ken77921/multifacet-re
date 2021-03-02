import argparse
import torch
import sys
import random
import os
import numpy as np
sys.path.insert(0, sys.path[0]+'/..')
#sys.path.append("..")
import utils.utils as utils
from collections import Counter
import pandas as pd
import pickle
from matplotlib import pyplot as plt

#remove the duplicated sentences
#remove the sentences which are too long
#remove stop words in target
#handle the min target filtering (If more than 30 words in output, just do random sampling)
#padding and store them into tensors, (random shuffle? two sets), store train, val, and test

parser = argparse.ArgumentParser(description='Preprocessing step 2')
parser.add_argument('--data', type=str, default='./data/processed/',
                    help='location of the data corpus')
parser.add_argument('--save', type=str, default='./data/processed/wackypedia/tensors/',
                    help='path to save the output data')
parser.add_argument('--max_sent_len', type=int, default=50,
                    help='max sentence length for input features')
parser.add_argument('--multi_sent', default=False,
                    help='Whether do we want to cram multiple sentences into one input feature')
parser.add_argument('--max_target_num', type=int, default=30,
                    help='max word number for output prediction w/o stop words (including above and below sentences)')
parser.add_argument('--max_sent_num', type=int, default='100000000000',
                    help='load only this number of sentences from input corpus')
parser.add_argument('--seed', type=int, default=1111,
                    help='random seed')
parser.add_argument('--val_size_ratio', type=float, default=0.05,
                    help='Ratio of dataset to set as val set')
parser.add_argument('--fixed_var_basis', default=False, action='store_true',
                    help='create fixed variable basis instead of freq based dynamic basis')
parser.add_argument('--stop_word_file', type=str, default='./resources/stop_word_list',
                    help='path to the file of a stop word list')

args = parser.parse_args()

print(args)

random.seed(args.seed)

if not os.path.exists(args.save):
    os.makedirs(args.save)

def convert_stop_to_ind(f_in, w_d2_ind_freq):
    stop_word_set = set()
    for line in f_in:
        w = line.rstrip()
        if w in w_d2_ind_freq:
            stop_word_set.add(w_d2_ind_freq[w][0])
    return stop_word_set

def convert_stop_to_ind_lower(f_in, idx2word_freq):
    stop_word_org_set = set()
    for line in f_in:
        w = line.rstrip()
        stop_word_org_set.add(w)
    stop_word_set = set()
    for idx, (w, freq) in enumerate(idx2word_freq):
        if w.lower() in stop_word_org_set:
            stop_word_set.add(idx)
    return stop_word_set
        
def load_ind(f_pin, f_tin, max_sent_num, max_sent_len, max_target_num):
    w_ind_corpus = []
    t_ind_corpus = []
    kb_w_ind_corpus = []
    kb_t_ind_corpus = []
    unique_patterns_ind = []
    unique_patterns_count = []
    entpair_freq = []

    kb_unique_patterns_ind = []
    kb_unique_patterns_count = []
    kb_entpair_freq = []

    # last_sent = ''
    # num_duplicated_sent = 0
    num_too_long_sent = 0
    num_targets_too_long = 0
    num_duplicated_for_targets = 0
    
    for pline, tline in zip(f_pin, f_tin):
        current_sent = pline.rstrip()
        current_targets = tline.rstrip()
        # if current_sent == last_sent:
        #     num_duplicated_sent += 1
        #     continue        
        # last_sent = current_sent
        fields = current_sent.split(' ')
        if len(fields) > max_sent_len:
            num_too_long_sent += 1
            continue
        kb = (len(fields) == 2) # and fields.index(colon_idx) != -1)
        if kb:
            kb_unique_patterns_ind.append(len(kb_w_ind_corpus))
        else:
            unique_patterns_ind.append(len(w_ind_corpus))
        targets = [int(x) for x in current_targets.split(' ')]
        sent = [int(x) for x in fields]
        num_entpairs = 0
        if (len(targets) > max_target_num):  
            num_targets_too_long += 1 
            num_repeated = 0         
            for i in range(0,len(targets),max_target_num):
                num_duplicated_for_targets += 1
                num_repeated += 1
                if kb:
                    kb_t_ind_corpus.append(targets[i:i+max_target_num])
                    kb_w_ind_corpus.append(sent)
                    num_entpairs += len(kb_t_ind_corpus[-1])
                else:
                    t_ind_corpus.append(targets[i:i+max_target_num])                
                    w_ind_corpus.append(sent)
                    num_entpairs += len(t_ind_corpus[-1])
                total_len = len(w_ind_corpus) + len(kb_w_ind_corpus)
                if total_len % 1000000 == 0:
                    print(total_len)
                    sys.stdout.flush()
                if total_len > max_sent_num:
                    break
            if kb:
                kb_unique_patterns_count.append(num_repeated)    
            else:
                unique_patterns_count.append(num_repeated)
        else:
            if kb:
                kb_w_ind_corpus.append(sent)
                kb_t_ind_corpus.append(targets)
            else:
                w_ind_corpus.append(sent)
                t_ind_corpus.append(targets)
            num_entpairs = len(targets)
            total_len = len(w_ind_corpus) + len(kb_w_ind_corpus)
            if total_len % 1000000 == 0:
                print(total_len)
                sys.stdout.flush()
            if kb:
                kb_unique_patterns_count.append(1)
            else:
                unique_patterns_count.append(1)
        if kb:
            kb_entpair_freq.append(num_entpairs)
        else:
            entpair_freq.append(num_entpairs)
        if total_len > max_sent_num:
            break

    assert len(unique_patterns_ind) == len(unique_patterns_count), "Unique index list and Unique count list have diffferent sizes!"
    assert len(unique_patterns_ind) == len(entpair_freq), "Unique index list and entpair freq list have diffferent sizes!"
    assert len(kb_unique_patterns_ind) == len(kb_entpair_freq), "KB unique index list and KB entpair freq list have diffferent sizes!"

    print("Finish loading {} sentences. While removing {} long sentences".format(len(w_ind_corpus), num_too_long_sent))
    print("{} sentences duplicated because targets are too long".format(num_duplicated_for_targets))

    return w_ind_corpus, t_ind_corpus, unique_patterns_ind, unique_patterns_count, entpair_freq,\
        kb_w_ind_corpus, kb_t_ind_corpus, kb_unique_patterns_ind, kb_unique_patterns_count, kb_entpair_freq

corpus_input_name = os.path.join(args.data, "pattern_index")
dictionary_input_name = os.path.join(args.data, "pattern_dictionary_index")
targets_input_name = os.path.join(args.data, "entpair_index")
entpair_dictionary_name = os.path.join(args.data, "entpair_dictionary_index")

#with open(dictionary_input_name) as f_in:
#    w_d2_ind_freq, max_ind = utils.load_word_dict(f_in)

with open(dictionary_input_name) as f_in:
    idx2word_freq = utils.load_idx2word_freq(f_in)

max_ind = len(idx2word_freq)

if max_ind >= 2147483648:
    print("Will cause overflow")
    sys.exit()

store_type = torch.int32

with open(args.stop_word_file) as f_in:
    #stop_ind_set = convert_stop_to_ind(f_in, w_d2_ind_freq)
    stop_ind_set = convert_stop_to_ind_lower(f_in, idx2word_freq)

with open(corpus_input_name) as f_pin, open(targets_input_name) as f_tin:
    w_ind_corpus, t_ind_corpus, unique_patterns_ind, unique_patterns_count,entpair_freq,\
        kb_w_ind_corpus, kb_t_ind_corpus, kb_unique_patterns_ind, kb_unique_patterns_count, kb_entpair_freq = \
            load_ind(f_pin, f_tin, args.max_sent_num, args.max_sent_len, args.max_target_num)


dynamic_basis = not args.fixed_var_basis

corpus_size = len(w_ind_corpus) + len(kb_w_ind_corpus)
unique_patterns_ind = np.array(unique_patterns_ind) + len(kb_w_ind_corpus)
unique_patterns_count = np.array(unique_patterns_count)
print("Allocating {} bytes".format( corpus_size*(args.max_target_num+args.max_sent_len)*4 ) )
all_features = torch.zeros(corpus_size,args.max_sent_len,dtype = store_type)
all_targets = torch.zeros(corpus_size,args.max_target_num,dtype = store_type)
all_kb_markers = torch.zeros(corpus_size).to(torch.bool)
if dynamic_basis:
    all_entpair_log_freq = torch.zeros(corpus_size).to(torch.long)

random_selection_num = 0

cur = 0
for i in range(len(kb_w_ind_corpus)):
    feature_list = kb_w_ind_corpus[i]
    target_list = kb_t_ind_corpus[i]

    current_len = len(feature_list) - 1
    target_len = len(target_list)

    all_features[i,-(current_len+1):] = torch.tensor(feature_list, dtype=store_type)
    all_targets[i, :target_len] = torch.tensor(target_list, dtype=store_type)
    all_kb_markers[i] = 1
    if dynamic_basis and cur < len(kb_unique_patterns_ind) and i == kb_unique_patterns_ind[cur]:
        all_entpair_log_freq[i:i + kb_unique_patterns_count[cur]] = np.ceil(np.log(kb_entpair_freq[cur]))
        cur += 1

j = 0
cur = 0
for i in range(len(kb_w_ind_corpus), corpus_size):
    feature_list = w_ind_corpus[j]
    target_list = t_ind_corpus[j]        
    current_len = len(feature_list) - 1
    target_len = len(target_list)

    all_features[i,-(current_len+1):] = torch.tensor(feature_list,dtype = store_type)
    all_targets[i, :target_len] = torch.tensor(target_list, dtype=store_type)
    all_kb_markers[i] = 0
    if dynamic_basis and cur < len(unique_patterns_ind) and j == unique_patterns_ind[cur]:
        all_entpair_log_freq[i:i + unique_patterns_count[cur]] = np.ceil(np.log(entpair_freq[cur]))
        cur += 1
    j = j + 1

del w_ind_corpus

print("{} / {} needs to randomly select targets".format(random_selection_num,corpus_size))

# Partition the dataset and save
def store_tensors(f_out,tensor1,tensor2, tensor3=None, tensor4=None):
    torch.save([tensor1,tensor2,tensor3,tensor4], f_out)

def store_dataset_freq(start_inds, counts, epfreq, filename, pattern_strings=None):
    stats = dict(zip(start_inds, list(zip(counts, epfreq))))
    df = pd.DataFrame.from_dict(stats, orient='index', columns=['Count', 'Entity Pair Frequency'])
    if pattern_strings is not None:
        df['Pattern String'] = pattern_strings
    df = df.sort_values('Count', ascending=False)
    df.to_csv(filename, sep='\t')

def to_string(patterns):
    pattern_strings = []
    for pattern in patterns:
        pattern_words = []
        for ind in pattern:
            if ind != 0:
                pattern_words.append(idx2word_freq[ind.item()][0])
        pattern_strings.append(' '.join(pattern_words))
    return pattern_strings

entpair_freq = np.array(entpair_freq)
kb_entpair_freq = np.array(kb_entpair_freq)

training_output_name = os.path.join(args.save, "train.pt")
# val_org_output_name = args.save + "val_org.pt"
val_shuffled_output_name = os.path.join(args.save, "val_shuffled.pt")

val_size_ratio = args.val_size_ratio
assert 0 <= val_size_ratio < 0.5, "Validation set should not be more than 50% of the corpus size!"

num_unique_corpus_patterns = len(unique_patterns_ind)
val_size = int(num_unique_corpus_patterns * val_size_ratio)
dataset_size = 0
if val_size > 0:
    # NOTE: We add the original val set to the train set later on
    # with open(val_org_output_name,'wb') as f_out:
    val_unique_start_ind, val_unique_counts, val_unique_ep_freq = unique_patterns_ind[-val_size:], unique_patterns_count[-val_size:], entpair_freq[-val_size:]
    val_org_indices = [idx for start, count in zip(val_unique_start_ind, val_unique_counts) for idx in range(start, start+count)]
    print("Validation set size(non-shuffled - added to train set): {} (unique: {})".format(len(val_org_indices), val_size))

    rest_size = num_unique_corpus_patterns - val_size
    shuffle_ind = np.array(range(rest_size))
    random.shuffle(shuffle_ind)

    with open(val_shuffled_output_name,'wb') as f_out:
        shuffled_val_ind = shuffle_ind[-val_size:]
        val_shuffled_unique_start_ind, val_shuffled_unique_counts, val_shuffled_ep_freq = unique_patterns_ind[shuffled_val_ind], unique_patterns_count[shuffled_val_ind], entpair_freq[shuffled_val_ind]
        store_ind = [idx for start, count in zip(val_shuffled_unique_start_ind, val_shuffled_unique_counts) for idx in range(start, start+count)]
        dataset_size += len(store_ind)
        print("Shuffled Validation set size: {} (unique:{})".format(len(store_ind), val_size))
        val_shuffled_pattern_strings = to_string(all_features[val_shuffled_unique_start_ind, :])
        store_dataset_freq(val_shuffled_unique_start_ind, val_shuffled_unique_counts, val_shuffled_ep_freq, os.path.join(args.data, "val_shuffled_counter.txt"), val_shuffled_pattern_strings)
        store_tensors(f_out,all_features[store_ind,:],all_targets[store_ind,:], all_kb_markers[store_ind], all_entpair_log_freq[store_ind] if dynamic_basis else None)

    with open(training_output_name,'wb') as f_out:
        shuffled_train_ind = shuffle_ind[:rest_size-val_size]
        train_unique_start_ind, train_unique_counts, train_unique_ep_freq = unique_patterns_ind[shuffled_train_ind], unique_patterns_count[shuffled_train_ind], entpair_freq[shuffled_train_ind]
        store_ind = [idx for start, count in zip(train_unique_start_ind, train_unique_counts) for idx in range(start, start+count)]
        store_ind = store_ind + val_org_indices + list(range(len(kb_w_ind_corpus)))

        train_start_inds = np.concatenate([train_unique_start_ind, val_unique_start_ind, kb_unique_patterns_ind], axis=None)
        train_counts = np.concatenate([train_unique_counts, val_unique_counts, kb_unique_patterns_count], axis=None)
        train_ep_freqs = np.concatenate([train_unique_ep_freq, val_unique_ep_freq, kb_entpair_freq], axis=None)
        dataset_size += len(store_ind)
        print("Training set size: {} (unique:{})".format(len(store_ind), len(train_start_inds)))

        train_pattern_strings = to_string(all_features[train_start_inds, :])
        store_dataset_freq(train_start_inds, train_counts, train_ep_freqs, os.path.join(args.data, "train_counter.txt"), train_pattern_strings)
        store_tensors(f_out,all_features[store_ind,:],all_targets[store_ind,:], all_kb_markers[store_ind], all_entpair_log_freq[store_ind] if dynamic_basis else None)
else:
    shuffled_train_ind = np.array(range(num_unique_corpus_patterns))
    random.shuffle(shuffled_train_ind)
    with open(training_output_name, 'wb') as f_out:
        train_unique_start_ind, train_unique_counts, train_unique_ep_freq = unique_patterns_ind[shuffled_train_ind], \
                                                                            unique_patterns_count[shuffled_train_ind], \
                                                                            entpair_freq[shuffled_train_ind]
        store_ind = [idx for start, count in zip(train_unique_start_ind, train_unique_counts) for idx in
                     range(start, start + count)]
        store_ind = store_ind + list(range(len(kb_w_ind_corpus)))

        train_start_inds = np.concatenate([train_unique_start_ind, kb_unique_patterns_ind], axis=None)
        train_counts = np.concatenate([train_unique_counts, kb_unique_patterns_count], axis=None)
        train_ep_freqs = np.concatenate([train_unique_ep_freq, kb_entpair_freq], axis=None)
        dataset_size += len(store_ind)
        print("Training set size: {} (unique:{})".format(len(store_ind), len(train_start_inds)))

        train_pattern_strings = to_string(all_features[train_start_inds, :])
        store_dataset_freq(train_start_inds, train_counts, train_ep_freqs, os.path.join(args.data, "train_counter.txt"),
                           train_pattern_strings)
        store_tensors(f_out, all_features[store_ind, :], all_targets[store_ind, :], all_kb_markers[store_ind],
                      all_entpair_log_freq[store_ind] if dynamic_basis else None)

assert dataset_size == corpus_size, "Corpus size and dataset size(train + val_shuffled + test + test_shuffled) do not match!"


kb_freq_counts = np.bincount(np.ceil(np.log(kb_entpair_freq)).astype(dtype=np.int))
plt.bar(np.arange(len(kb_freq_counts)), kb_freq_counts, edgecolor='black', linewidth=1.2)
plt.ylabel("No. of KB relations")
plt.xlabel("Entity Pair Log Frequency")
plt.xticks(np.arange(len(kb_freq_counts)))
plt.title("No. of KB Relations vs Entity Pair Log Freq")
plt.tight_layout()
plt.savefig(os.path.join(args.save, "kb_freq_plot.png"))
print("Unique KBs: {}".format(len(kb_entpair_freq)))

plt.clf()

sentp_freq_counts = np.bincount(np.ceil(np.log(entpair_freq)).astype(dtype=np.int))
plt.bar(np.arange(len(sentp_freq_counts)), sentp_freq_counts, edgecolor='black', linewidth=1.2)
plt.ylabel("No. of sentence patterns")
plt.xlabel("Entity Pair Log Frequency")
plt.xticks(np.arange(len(sentp_freq_counts)))
plt.title("No. of sentence patterns vs Entity Pair Log Freq")
plt.tight_layout()
plt.savefig(os.path.join(args.save, "sentp_freq_plot.png"))
print("Unique Sentence Patterns: {}".format(len(entpair_freq)))