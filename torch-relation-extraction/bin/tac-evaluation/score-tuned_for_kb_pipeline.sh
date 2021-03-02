#!/usr/bin/env bash

CANDIDATES=$1
MODEL=$2
VOCAB=$3
GPU=$4
MAX_SEQ=$5
TUNED_PARAMS=$6
OUT=$7
EVAL_ARGS=${@:8}

TAC_EVAL_ROOT=${TH_RELEX_ROOT}/bin/tac-evaluation

#QUERY_EXPANDED=${RUN_DIR}/query_expanded.xml

mkdir -p ${OUT}

# score candidate file

source ${TAC_EVAL_ROOT}/scoring_function.sh ${CANDIDATES} ${OUT} ${VOCAB} ${MODEL} $GPU $MAX_SEQ $EVAL_ARGS

# threshold candidate file using tuned params
#THRESHOLD_CANDIDATE=`mktemp`
THRESHOLD_CANDIDATE="${OUT}/threshold_candidate"
echo "Thresholding candidate file :"
echo "${TAC_EVAL_ROOT}/eval-scripts/threshold-scored-candidates.sh ${SCORED_CANDIDATES} ${TUNED_PARAMS} ${THRESHOLD_CANDIDATE}"
${TAC_EVAL_ROOT}/eval-scripts/threshold-scored-candidates.sh ${SCORED_CANDIDATES} ${TUNED_PARAMS} ${THRESHOLD_CANDIDATE}

