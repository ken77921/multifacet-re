#!/bin/bash

conf=$1 # the config file used for scoring
checkpoint=$2 # the model checkpoitn directory - must be one of the epoch dirs
outdir=$3 # the output dir where the embeddings will be stored

source $conf

if [[ -z "${randomness}" ]]
then
    randomness=""
else
    if [[ "${randomness}" == true ]]
    then
        randomness="--randomness True"
    else
        randomness="--randomness False"
    fi
fi

$PY_PATH -u src/testing/get_kb_embs.py --data $data --entpair_vocab_map ${data%/}/entpair-new-vocab.txt --n_basis ${basis_arr[0]} --n_basis_kb $n_basis_kb --checkpoint $checkpoint --batch_size 200 --de_model $dec_type --en_model $enc_type $randomness  --encode_trans_layers $enc_layers --trans_layers $dec_layers --seed $seed --outdir $outdir/kb_rels/
$PY_PATH -u src/testing/get_pattern_embs.py --data $data --entpair_vocab_map ${data%/}/entpair-new-vocab.txt --n_basis ${basis_arr[0]} --n_basis_kb $n_basis_kb --checkpoint $checkpoint --batch_size 1000 --de_model $dec_type --en_model $enc_type $randomness --encode_trans_layers $enc_layers --trans_layers $dec_layers --seed $seed --outdir $outdir/patterns/
