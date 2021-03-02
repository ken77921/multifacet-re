import argparse
import gzip
import os
import time
import sys
sys.path.insert(0, sys.path[0]+'/..')
from utils.utils import Dictionary, str2bool
from collections import OrderedDict
import pandas as pd

#map words to index (and set the max sentence number), 
#map low freq words into <unk>
#add end of sentence tokens (for transformer to generate output embedding), 
#output dataset, dictionary (start with <null>, <unk>, and <eos>), word frequency, print total number of words, total number of filtered words

parser = argparse.ArgumentParser(description='Preprocessing step 1')
parser.add_argument('--data', type=str, default='./data/patterns.txt',
                    help='location of the sorted sentence patterns and their entity pairs')
parser.add_argument('--epvocab', type=str, default='./data/train.vocab-entpairs.txt',
                    help='location of the entity pairs')
parser.add_argument('--save', type=str, default='./data/processed/wackypedia/',
                    help='path to save the output data')
parser.add_argument('--min_freq', type=int, default='5',
                    help='map to <unk> if observe less than this number')
parser.add_argument('--min_sent_length', type=int, default='5',
                    help='skip the sentence if sentence length is less than this number')
parser.add_argument('--max_sent_num', type=int, default='100000000000000',
                    help='load only this number of sentences from input corpus')
parser.add_argument('--lowercase', type=str2bool, nargs='?', default=False,
                    help='whether make all the words in corpus lowercased')

args = parser.parse_args()

print(args)

if not os.path.exists(args.save):
    os.makedirs(args.save)

start_time_patterns = time.time()
one_word_patterns = {}
if args.data[-3:] == '.gz':
    my_open = gzip.open
    byte_mode = True
else:
    my_open = open
    byte_mode = False

pattern2entpair = OrderedDict()
with open(args.data) as fin:      
    for line in fin:
        parts = line.rstrip('\n').split('\t')
        if len(parts) == 0: continue
        if parts[0] not in pattern2entpair:
            pattern2entpair[parts[0]] = []
        pattern2entpair[parts[0]].append(tuple((parts[1], parts[2])))

print('{} patterns'.format(len(pattern2entpair)))
w_ind_corpus = []
        
dict_c = Dictionary(byte_mode)

total_num_w = 0
filtered_sent_num = 0

for w_list_org, entpairs in pattern2entpair.items():
    w_list_org = w_list_org.rstrip().split()
    if 0 <= len(w_list_org) < args.min_sent_length or len(entpairs) == 0:
        filtered_sent_num += 1
        continue
    if len(w_list_org) == 1:
        one_word_patterns[w_list_org[0]] = len(entpairs)
    w_ind_list = []
    for w in w_list_org:
        if args.lowercase:
            w = w.lower()
        w_ind = dict_c.dict_check_add(w)
        w_ind_list.append(w_ind)
        total_num_w += 1
    dict_c.append_eos(w_ind_list)
    w_ind_corpus.append(w_ind_list)
    if len(w_ind_corpus) % 1000000 == 0:
        print(len(w_ind_corpus))
        sys.stdout.flush()
    if len(w_ind_corpus) >= args.max_sent_num:
        break

df = pd.DataFrame.from_dict(one_word_patterns, orient='index', columns=['Count'])
df.index.name = 'Pattern'
df.to_csv(os.path.join(args.save, 'single_word_patterns.txt'), sep='\t')
print(df.shape[0], 'single word patterns.')

print("total number of patterns: "+str(len(w_ind_corpus)))
elapsed_patterns = time.time() - start_time_patterns
print("time of loading pattern file: "+str(elapsed_patterns)+'s')

compact_mapping, total_freq_filtering = dict_c.densify_index(args.min_freq)
print("{}/{} tokens are filtered".format(total_freq_filtering, total_num_w) )

corpus_output_name = os.path.join(args.save, "pattern_index")
dictionary_output_name = os.path.join(args.save, "pattern_dictionary_index")
entpair_output_name = os.path.join(args.save, "entpair_index")
entpair_dictionary_name = os.path.join(args.save, "entpair_dictionary_index")

with open(dictionary_output_name, 'w') as f_out:
    dict_c.store_dict(f_out)

with open(corpus_output_name, 'w') as f_out:
    for w_ind_list in w_ind_corpus:
         f_out.write(' '.join([str(compact_mapping[x]) for x in w_ind_list])+'\n')

#  the entity pair vocab - add [null] at index 0
epvocab = OrderedDict()
epvocab['[null]'] = 0
start_time_epvocab = time.time()
with open(args.epvocab, 'r') as fin:    
    num_ep = 0
    for entpair_ind in fin:
        num_ep += 1
        parts = entpair_ind.split("\t")
        epvocab[tuple((parts[0], parts[1]))] = int(parts[2])
elapsed_epvocab = time.time() - start_time_epvocab
assert len(epvocab) == num_ep+1, "Count of entity pairs read from file not same as those in vocab"
print("{} entity pairs read, time taken = {}s".format(num_ep, elapsed_epvocab))

dict_ep = {}
num_targets = 0
with open(entpair_output_name, 'w') as fout:
    for entpair_list in pattern2entpair.values():
        num_targets += 1
        entpair_ind_list = []
        for entpair in entpair_list:
            if entpair not in dict_ep: 
                dict_ep[entpair] = [0, epvocab[entpair]]
            dict_ep[entpair][0] += 1
            entpair_ind_list.append(epvocab[entpair])
        print(*entpair_ind_list, file=fout)
    print("{} target indices written to file".format(num_targets))

with open(entpair_dictionary_name, 'w') as fout:
    for entpair, index in epvocab.items():
        if entpair == '[null]':
            fout.write('ep{}\t{}\t{}\n'.format(index, -1, index))
        else:    
            fout.write('ep{}\t{}\t{}\n'.format(index, dict_ep[entpair][0], index))

elapsed_total = time.time() - start_time_patterns
print("time of total word to index: "+str(elapsed_total)+'s')
