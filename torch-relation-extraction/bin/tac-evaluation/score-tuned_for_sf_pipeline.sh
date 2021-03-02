#!/usr/bin/env bash

CANDIDATES=$1
QUERY_EXPANDED=$2
MODEL=$3
VOCAB=$4
GPU=$5
MAX_SEQ=$6
TUNED_PARAMS=$7
OUT=$8
EVAL_ARGS=${@:9}

TAC_EVAL_ROOT=${TH_RELEX_ROOT}/bin/tac-evaluation

#QUERY_EXPANDED=${RUN_DIR}/query_expanded.xml

mkdir -p ${OUT}

# score candidate file

source ${TAC_EVAL_ROOT}/scoring_function.sh ${CANDIDATES} ${OUT} ${VOCAB} ${MODEL} $GPU $MAX_SEQ $EVAL_ARGS
##SCORED_CANDIDATES=`mktemp`
#SCORED_CANDIDATES="${OUT}/scored_candidates"
#CAND_SCORE_CMD="/home/hschang/torch/install/bin/th ${TH_RELEX_ROOT}/src/eval/ScoreCandidateFile.lua -candidates $CANDIDATES -vocabFile $VOCAB -model $MODEL -gpuid $GPU -threshold 0 -outFile $SCORED_CANDIDATES -maxSeq $MAX_SEQ $EVAL_ARGS"
#echo "Scoring candidate file: ${CAND_SCORE_CMD}"
#${CAND_SCORE_CMD}

# threshold candidate file using tuned params
#THRESHOLD_CANDIDATE=`mktemp`
THRESHOLD_CANDIDATE="${OUT}/threshold_candidate"
echo "Thresholding candidate file :"
echo "${TAC_EVAL_ROOT}/eval-scripts/threshold-scored-candidates.sh ${SCORED_CANDIDATES} ${TUNED_PARAMS} ${THRESHOLD_CANDIDATE}"
${TAC_EVAL_ROOT}/eval-scripts/threshold-scored-candidates.sh ${SCORED_CANDIDATES} ${TUNED_PARAMS} ${THRESHOLD_CANDIDATE}

# convert scored candidate to response file
echo "Converting scored candidate to response file"
#RESPONSE=`mktemp`
RESPONSE="${OUT}/response"
#${TAC_ROOT}/components/bin/response.sh $QUERY_EXPANDED ${THRESHOLD_CANDIDATE} ${RESPONSE}
echo "${TAC_ROOT}/components/bin/response_inv.sh ${QUERY_EXPANDED} ${THRESHOLD_CANDIDATE} ${RESPONSE}"
${TAC_ROOT}/components/bin/response_inv.sh ${QUERY_EXPANDED} ${THRESHOLD_CANDIDATE} ${RESPONSE}

#echo "Post processing response for year $YEAR"
#RESPONSE_PP=`mktemp`
#RESPONSE_PP="${OUT}/response_pp${YEAR}"
#${TAC_EVAL_ROOT}/post-process-response.sh $YEAR $PP $QUERY_EXPANDED $RESPONSE $RESPONSE_PP


#cp $RESPONSE $OUT
