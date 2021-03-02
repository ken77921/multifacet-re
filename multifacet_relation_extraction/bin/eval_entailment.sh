#!/bin/bash
OUTDIR=$1
PAT_BASIS=$2
BASELINE_EMB=$3
$PY_PATH src/testing/eval_entailment.py --emb_dir output/${OUTDIR} --wordnet_patterns ../dataset/RE_entailment_labels_test.tsv --pat_emb $BASELINE_EMB --save entailment_scores.txt --batch_size 500
