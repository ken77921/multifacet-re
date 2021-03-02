#!/bin/bash
OUTDIR=$1
PAT_BASIS=$2
$PY_PATH src/testing/get_entailment_scores.py --emb_dir output/${OUTDIR} --save entailment_scores.txt --batch_size 500 --n_basis ${PAT_BASIS}
