#!/usr/bin/env bash

YEAR=$1
MODEL=$2
VOCAB=$3
GPU=$4
MAX_SEQ=$5
OUT=$6
EVAL_ARGS=${@:7}


TAC_EVAL_ROOT=${TH_RELEX_ROOT}/bin/tac-evaluation
source ${TAC_EVAL_ROOT}/configs/${YEAR}

TMPDIR=/iesl/canvas/hschang/temp
# score candidate file
SCORED_CANDIDATES=`mktemp -p $TMPDIR`
CAND_SCORE_CMD="/home/hschang/torch/install/bin/th ${TH_RELEX_ROOT}/src/eval/ScoreCandidateFile.lua -candidates $CANDIDATES -vocabFile $VOCAB -model $MODEL -gpuid $GPU -threshold 0 -outFile $SCORED_CANDIDATES -maxSeq $MAX_SEQ $EVAL_ARGS"
echo "Scoring candidate file: ${CAND_SCORE_CMD}"
${CAND_SCORE_CMD}

# tune thresholds with scored file
echo "${TH_RELEX_ROOT}/bin/tac-evaluation/tune-thresh-prescored_es.sh $YEAR $SCORED_CANDIDATES $OUT"
${TH_RELEX_ROOT}/bin/tac-evaluation/tune-thresh-prescored_es.sh $YEAR $SCORED_CANDIDATES $OUT
