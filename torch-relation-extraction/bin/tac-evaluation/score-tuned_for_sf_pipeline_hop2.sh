#!/usr/bin/env bash

CANDIDATES=$1
HOP2_QUERY_EXPANDED=$2
HOP2_QUERY_ORG=$3
MODEL=$4
VOCAB=$5
GPU=$6
MAX_SEQ=$7
TUNED_PARAMS=$8
HOP1_TUNED_PARAMS=$9
HOP1_RESPONSE=${10}
OUT=${11}
EVAL_ARGS=${@:12}

TAC_EVAL_ROOT=${TH_RELEX_ROOT}/bin/tac-evaluation

#HOP2_QUERY_EXPANDED=${RUN_DIR}/query_expanded.xml

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

REL_NOT_HANDLED=/iesl/canvas/hschang/TAC_2016/codes/tackbp2016-kb/config/rel_not_handled_list
INV_REL_CONFIG=/iesl/canvas/hschang/TAC_2016/codes/tackbp2016-kb/config/coldstart_relations2015_inverses.config


# convert scored candidate to response file
echo "Converting scored candidate to response file"
#RESPONSE=`mktemp`
RESPONSE="${OUT}/response"
#${TAC_ROOT}/components/bin/response.sh $HOP2_QUERY_EXPANDED ${THRESHOLD_CANDIDATE} ${RESPONSE}
echo "${TAC_ROOT}/components/bin/response_inv.sh ${HOP2_QUERY_EXPANDED} ${THRESHOLD_CANDIDATE} ${RESPONSE}"
${TAC_ROOT}/components/bin/response_inv.sh ${HOP2_QUERY_EXPANDED} ${THRESHOLD_CANDIDATE} ${RESPONSE}

RESPONSE_HOP1="${OUT}/response_hop1_filtering"
echo "python ${TAC_EVAL_ROOT}/eval-scripts/filter_using_hop1_thresholds.py ${RESPONSE} $HOP2_QUERY_ORG $HOP1_RESPONSE $REL_NOT_HANDLED $INV_REL_CONFIG ${HOP1_TUNED_PARAMS} ${RESPONSE_HOP1}"
python ${TAC_EVAL_ROOT}/eval-scripts/filter_using_hop1_thresholds.py ${RESPONSE} $HOP2_QUERY_ORG $HOP1_RESPONSE $REL_NOT_HANDLED $INV_REL_CONFIG ${HOP1_TUNED_PARAMS} ${RESPONSE_HOP1}
#echo "Post processing response for year $YEAR"
#RESPONSE_PP=`mktemp`
#RESPONSE_PP="${OUT}/response_pp${YEAR}"
#${TAC_EVAL_ROOT}/post-process-response.sh $YEAR $PP $HOP2_QUERY_EXPANDED $RESPONSE $RESPONSE_PP


#cp $RESPONSE $OUT
