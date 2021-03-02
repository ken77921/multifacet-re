## Create directories
```
mkdir data
mkdir resources
mkdir models
mkdir logs
```

## Setup dependencies
Install anaconda3 and setup a conda environment. The conda environment we used for training/testing has been exported in mfre.yml.
```
conda env create --name mfre -f mfre.yml 
conda activate mfre
```

## Download resource and data files
- Download the data files from [here](https://drive.google.com/file/d/1gqptnAY5FLO0sSEXg0tv6nLcCqgvYCJB/view?usp=sharing), unzip and extract them into the `data` folder.  
- Download the resource files from [here](https://drive.google.com/file/d/1hkzi2lvtFpnxW3Q0mD_AWw8Xa37vPchU/view?usp=sharing), unzip and extract them into the `resources` folder

**NOTE:** `train_sorted_patterns.txt` can be produced by running `awk -F $'\t' '{print $3"\t"$1"\t"$2}' train_sorted.ds | sort -t $'\t' -k1,1 -k2,2 -k3,3 > train_sorted_patterns.txt` on [`train_sorted.ds`](https://drive.google.com/file/d/1Su2pGqYOYUstTqqlIIQVjjlPDqGmZ8U-/view?usp=sharing) and `train_sorted.ds` comes from Verga et al., 2016.
But unfortunately, the output of this command depends on the OS and the locale active on the OS, so we have provided the file which produced the results reported in our paper.

**NOTE:** `pytorch-entpair-embfile.txt` contains entity pair embeddings of Universal Schema. Please refer to `../torch-relation-extraction/README.md` for the steps of training Universal Schema.

## Export the conda environment python path
Point `PY_PATH` to your python path. For example, 
`export PY_PATH=~/miniconda3/envs/mfre/bin/python`

## Export the path to the data directory
`export DATA_DIR=./data/train_data`
where `train_data` is the name of the directory containing the data for training and subsequently, scoring.

## Prepare the training data
- Convert the data to indices: 
```
python src/preprocessing/map_tokens_to_indices.py \
  --data data/train_sorted_patterns.txt \
  --epvocab data/train.vocab-entpairs.txt \ 
  --save "${DATA_DIR}" \
  --min_sent_length 1 \
  --min_freq 1
```  
- Convert the indices to tensors:
```
python src/preprocessing/map_indices_to_tensors.py \
  --data "${DATA_DIR}" \
  --save "${DATA_DIR%/}"/tensors/ \ 
  --max_sent_len 20 \
  --max_target_num 5 \
  --val_size_ratio 0.05 \ 
  --fixed_var_basis
```  
## Train the model
```
./bin/train.sh \
configs/milestone_runs/train/b5kb11-l3-norands11-auto_sgd_pt1-auto_pt2_tgtlr1_maxopt.conf \
milestone_run_trans-b5-kb11
```
**NOTE:** Run the code on a machine with **at least 40GB RAM** and with a GPU **having at least 11GB memory** to train the model.

## Score the TAC candidate files
- Download the TAC candidate files from [here](https://drive.google.com/file/d/1_R55FH-Iitmhgz3zEiUqKxjp896bVn6D/view?usp=sharing), unzip and extract in the data folder.
- Run the scoring script to generate the scored candidate files for each year (2012, 2013, 2014) and for each model (best model till epochs 15, 20, 25, 30, 50):

```
./bin/score.sh \
configs/milestone_runs/score/trans_l3_no_rand_s11_b5.conf \
milestone_run_trans-b5-kb11 \
milestone_run_trans-b5-kb11
```

This script also needs to be run on a machine with at least 50GB of RAM (since multiple files are scored in parallel) and with a GPU having 11 GB of memory. 
- Convert the scored candidate files into format required by the evaluation scripts. Change the script to have the output folder name as in the previous step:
`./bin/convert.sh`
  
## Evaluation of TAC
Please refer to `../README.md`

## Entailment scoring and evaluation
- Download the entailment dataset created by using wordnet and our train+val sets [here](https://drive.google.com/file/d/12olFPxMeLigDk3weJroU5JAN14CqKvnZ/view?usp=sharing), unzip and extract them into the `data` folder.
- Download a preprocessed version of the [vocab file](https://drive.google.com/file/d/1siZoqPTJ68Eo4rbOLSndGtc_qErdiSDH/view?usp=sharing) and copy it into `data/train_data`.
- Run:
```
./bin/get_embs.sh \
configs/milestone_runs/score/trans_l3_no_rand_s11_b5.conf \
models/milestone_run_trans-b5-kb11-<timestamp>/ep50 \
output/milestone_run_trans-b5-kb11
```
This will prepare the kb relation and pattern embeddings needed for evaluating the entailment.
  
- Evaluate the entailment:
```
./bin/eval_entailment.sh \
milestone_run_trans-b5-kb11 \
5 \
data/CUSchema_scored_candidates
```
The scores are in `entailment_scores.txt` in the current folder.

## Figure reported in our paper
The code used to produce the figure reported in our paper can be found in `src/testing/Visualize.ipynb`.
