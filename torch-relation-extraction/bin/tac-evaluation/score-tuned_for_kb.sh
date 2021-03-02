#!/usr/bin/env bash

YEAR=$1
MODEL=$2
VOCAB=$3
GPU=$4
MAX_SEQ=$5
TUNED_PARAMS=$6
OUT=$7
EVAL_ARGS=${@:8}

TAC_EVAL_ROOT=${TH_RELEX_ROOT}/bin/tac-evaluation
source ${TAC_EVAL_ROOT}/configs/${YEAR}

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

## convert scored candidate to response file
#echo "Converting scored candidate to response file"
##RESPONSE=`mktemp`
#RESPONSE="${OUT}/response"
##${TAC_ROOT}/components/bin/response.sh $QUERY_EXPANDED ${THRESHOLD_CANDIDATE} ${RESPONSE}
#echo "${TAC_ROOT}/components/bin/response_inv.sh ${QUERY_EXPANDED} ${THRESHOLD_CANDIDATE} ${RESPONSE}"
#${TAC_ROOT}/components/bin/response_inv.sh ${QUERY_EXPANDED} ${THRESHOLD_CANDIDATE} ${RESPONSE}
#
#echo "Post processing response for year $YEAR"
##RESPONSE_PP=`mktemp`
#RESPONSE_PP="${OUT}/response_pp${YEAR}"
#${TAC_EVAL_ROOT}/post-process-response.sh $YEAR $PP $QUERY_EXPANDED $RESPONSE $RESPONSE_PP
#
#echo "Evaluating response"
#echo "`$SCORE_SCRIPT $RESPONSE_PP $KEY | tee ${OUT}/testing_result | grep -e F1 -e Recall -e Precision | tr '\n' '\t'`"
#
##cp $RESPONSE $OUT
