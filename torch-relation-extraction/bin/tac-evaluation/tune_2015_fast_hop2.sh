#!/bin/bash

candidates=$1
scored_candidates_dir=$2
hop2_query_expanded=$3
hop2_query_org=$4
hop1_params=$5
hop1_output_params=$6
hop2_output_params=$7
model=$8
vocab=$9
gpu=${10}
hop1_response=${11}
eval_args=${@:12}

export TAC_ROOT=/iesl/canvas/hschang/TAC_2016/codes/tackbp2016-sf
export TAC_CONFIG=$TAC_ROOT/config/coldstart2015_UMass_IESL1.config
export TH_RELEX_ROOT=/iesl/canvas/hschang/TAC_2016/codes/torch-relation-extraction

MAX_SEQ=20

mkdir -p $scored_candidates_dir


#CAND_SCORE_CMD="th ${TH_RELEX_ROOT}/src/eval/ScoreCandidateFile.lua -candidates $candidates -vocabFile $vocab -model $model -gpuid $gpu -threshold 0 -outFile $scored_candidates_dir/scored_candidates -maxSeq $MAX_SEQ $eval_args"
#echo $CAND_SCORE_CMD
#$CAND_SCORE_CMD
#${TAC_EVAL_ROOT}/eval-scripts/threshold-scored-candidates.sh $scored_candidates_dir/scored_candidates $hop1_params $scored_candidates_dir/threshold_candidate

#$TAC_ROOT/components/bin/response_inv.sh $hop2_query_expanded $scored_candidates_dir/threshold_candidate $scored_candidates_dir/response_full


#This filtering step ensure that the hop2 theshold cannot be lower than hop1. This would prevent some overfitting.
MAX_SEQ=20
${TH_RELEX_ROOT}/bin/tac-evaluation/score-tuned_for_sf_pipeline.sh $candidates $hop2_query_expanded $model $vocab $gpu $MAX_SEQ $hop1_params $scored_candidates_dir $eval_args

$TAC_ROOT/components/bin/postprocess2015.sh $scored_candidates_dir/response $hop2_query_expanded /dev/null $scored_candidates_dir/response_full_pp15

$TAC_ROOT/components/bin/response_cs_sf.sh $scored_candidates_dir/response_full_pp15 $scored_candidates_dir/response_full_pp15_noNIL

NUM_ITER=3
ASSESSMENTS=$TAC_ROOT/evaluation/resources/2015/batch_00_05_poolc.assessed.fqec

REL_NOT_HANDLED=/iesl/canvas/hschang/TAC_2016/codes/tackbp2016-kb/config/rel_not_handled_list
INV_REL_CONFIG=/iesl/canvas/hschang/TAC_2016/codes/tackbp2016-kb/config/coldstart_relations2015_inverses.config

mkdir -p `dirname $hop1_output_params`
mkdir -p `dirname $hop2_output_params`
python $TH_RELEX_ROOT/bin/tac-evaluation/eval-scripts/fast_threshold_tuning_2015_hop2.py $scored_candidates_dir/response_full_pp15_noNIL $hop1_response $hop2_query_org $ASSESSMENTS $REL_NOT_HANDLED $INV_REL_CONFIG $hop1_params $hop1_output_params $hop2_output_params $NUM_ITER

