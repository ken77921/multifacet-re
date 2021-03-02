#!/bin/bash

candidates=$1
scored_candidates_dir=$2
query_expanded=$3
init_params=$4
output_params=$5
model=$6
vocab=$7
gpu=$8
eval_args=${@:9}

export TAC_ROOT=/iesl/canvas/hschang/TAC_2016/codes/tackbp2016-sf
export TAC_CONFIG=$TAC_ROOT/config/coldstart2015_UMass_IESL1.config
export TH_RELEX_ROOT=/iesl/canvas/hschang/TAC_2016/codes/torch-relation-extraction

MAX_SEQ=20

mkdir -p $scored_candidates_dir

CAND_SCORE_CMD="th ${TH_RELEX_ROOT}/src/eval/ScoreCandidateFile.lua -candidates $candidates -vocabFile $vocab -model $model -gpuid $gpu -threshold 0 -outFile $scored_candidates_dir/scored_candidates -maxSeq $MAX_SEQ $eval_args"
echo $CAND_SCORE_CMD
$CAND_SCORE_CMD

$TAC_ROOT/components/bin/response_inv.sh $query_expanded $scored_candidates_dir/scored_candidates $scored_candidates_dir/response_full

$TAC_ROOT/components/bin/postprocess2015.sh $scored_candidates_dir/response_full $query_expanded /dev/null $scored_candidates_dir/response_full_pp15

$TAC_ROOT/components/bin/response_cs_sf.sh $scored_candidates_dir/response_full_pp15 $scored_candidates_dir/response_full_pp15_noNIL

NUM_ITER=3
ASSESSMENTS=$TAC_ROOT/evaluation/resources/2015/batch_00_05_poolc.assessed.fqec

mkdir -p `dirname $output_params`
python $TH_RELEX_ROOT/bin/tac-evaluation/eval-scripts/fast_threshold_tuning_2015.py $scored_candidates_dir/response_full_pp15_noNIL $ASSESSMENTS $init_params $output_params $NUM_ITER

