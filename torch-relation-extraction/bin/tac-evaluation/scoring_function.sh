#!/bin/bash

CANDIDATES=$1
OUT=$2
VOCAB=$3
MODEL=$4
GPU=$5
MAX_SEQ=$6
EVAL_ARGS=${@:7}

#SCORED_CANDIDATES=`mktemp`

#total_lines=$(wc -l <${$CANDIDATES})
#((lines_per_file = (total_lines + num_files - 1) / num_files))

TMPDIR=/iesl/canvas/hschang/temp

#To prevent out-of-memory error in lua
echo "Splitting the candidate file"
#CANDIDATE_SPLIT_DIR=${CANDIDATES}_split
CANDIDATE_SPLIT_DIR=`mktemp -d -p $TMPDIR`
rm -rf $CANDIDATE_SPLIT_DIR
mkdir -p $CANDIDATE_SPLIT_DIR
SPLIT_CMD="split -l 500000 $CANDIDATES $CANDIDATE_SPLIT_DIR/candidate_split"
echo $SPLIT_CMD
${SPLIT_CMD}

SCORED_CANDIDATES="${OUT}/scored_candidates"

>$SCORED_CANDIDATES

TEMP_SCORED_FILE="${OUT}/scored_candidate_piece"

for CANDIDATE_SUBSET in $CANDIDATE_SPLIT_DIR/*
do
    CAND_SCORE_CMD="/home/hschang/torch/install/bin/th ${TH_RELEX_ROOT}/src/eval/ScoreCandidateFile.lua -candidates $CANDIDATE_SUBSET -vocabFile $VOCAB -model $MODEL -gpuid $GPU -threshold 0 -outFile $TEMP_SCORED_FILE -maxSeq $MAX_SEQ $EVAL_ARGS"
    echo "Scoring candidate file: ${CAND_SCORE_CMD}"
    eval ${CAND_SCORE_CMD}
    cat $TEMP_SCORED_FILE >> $SCORED_CANDIDATES
done

rm $TEMP_SCORED_FILE
rm -rf $CANDIDATE_SPLIT_DIR
