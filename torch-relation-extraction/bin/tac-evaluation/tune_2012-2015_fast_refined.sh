#!/bin/bash

candidates=$1
scored_candidates_dir_parent=$2
query_expanded=$3
init_params=$4
output_params=$5
KDE_output_params=$6
model=$7
vocab=$8
gpu=$9
eval_args=${@:10}

scoring_output_all_years=$scored_candidates_dir_parent/scoring_output

export TAC_ROOT=/iesl/canvas/hschang/TAC_2016/codes/tackbp2016-sf
export TAC_CONFIG=$TAC_ROOT/config/coldstart2015_updated.config
export TH_RELEX_ROOT=/iesl/canvas/hschang/TAC_2016/codes/torch-relation-extraction
export TAC_EVAL_ROOT=${TH_RELEX_ROOT}/bin/tac-evaluation

mkdir -p $scored_candidates_dir_parent

>$scoring_output_all_years

MAX_SEQ=20

$TH_RELEX_ROOT/bin/tac-evaluation/generate_response_wo_threshold.sh 2012 $vocab $model $gpu $scored_candidates_dir_parent $MAX_SEQ $eval_args
$TH_RELEX_ROOT/bin/tac-evaluation/generate_response_wo_threshold.sh 2013 $vocab $model $gpu $scored_candidates_dir_parent $MAX_SEQ $eval_args
$TH_RELEX_ROOT/bin/tac-evaluation/generate_response_wo_threshold.sh 2014 $vocab $model $gpu $scored_candidates_dir_parent $MAX_SEQ $eval_args

scored_candidates_dir=$scored_candidates_dir_parent/2015
echo $scored_candidates_dir
mkdir -p $scored_candidates_dir

source ${TAC_EVAL_ROOT}/scoring_function.sh ${candidates} ${scored_candidates_dir} ${vocab} ${model} $gpu $MAX_SEQ $eval_args
#CAND_SCORE_CMD="th ${TH_RELEX_ROOT}/src/eval/ScoreCandidateFile.lua -candidates $candidates -vocabFile $vocab -model $model -gpuid $gpu -threshold 0 -outFile $scored_candidates_dir/scored_candidates -maxSeq $MAX_SEQ $eval_args"
#echo $CAND_SCORE_CMD
#$CAND_SCORE_CMD

$TAC_ROOT/components/bin/response_inv.sh $query_expanded $scored_candidates_dir/scored_candidates $scored_candidates_dir/response_full
$TAC_ROOT/components/bin/postprocess2015.sh $scored_candidates_dir/response_full $query_expanded /dev/null $scored_candidates_dir/response_full_pp15
$TAC_ROOT/components/bin/response_cs_sf.sh $scored_candidates_dir/response_full_pp15 $scored_candidates_dir/response_full_pp15_noNIL

ASSESSMENTS=$TAC_ROOT/evaluation/resources/2015/batch_00_05_poolc.assessed.fqec

RELCONFIG=/iesl/canvas/beroth/workspace/relationfactory_iesl/config/relations_coldstart2015.config
grep inverse $RELCONFIG \
| cut -d' ' -f1 \
| sed $'s#\(.*\)#\t\\1\t#g' \
> $scored_candidates_dir/inverses_with_tabs.tmp

REL_INV_CONFIG=/iesl/canvas/hschang/TAC_2016/codes/tackbp2016-kb/config/coldstart_relations2015_inverses.config

python $TH_RELEX_ROOT/bin/tac-evaluation/eval-scripts/scoring_outputs_for_tuning_2015.py $scored_candidates_dir/response_full_pp15_noNIL $ASSESSMENTS $scored_candidates_dir/scoring_output $scored_candidates_dir/inverses_with_tabs.tmp $REL_INV_CONFIG

cat $scored_candidates_dir/scoring_output >> $scoring_output_all_years

NUM_ITER=3

output_params_dir=`dirname $output_params`
mkdir -p $output_params_dir


PERFORMANCE_LOG=$output_params_dir/training_loss_log

KDE_dir=$scored_candidates_dir_parent/KDE

mkdir -p $KDE_dir

/home/hschang/anaconda2/bin/python $TH_RELEX_ROOT/bin/tac-evaluation/eval-scripts/KDE_accuracy_estimation_local.py $scoring_output_all_years $REL_INV_CONFIG $KDE_dir/accuracy_estimations

python $TH_RELEX_ROOT/bin/tac-evaluation/eval-scripts/tune_based_on_pred_distribution_2015.py $scored_candidates_dir/response_full_pp15_noNIL $scored_candidates_dir/inverses_with_tabs.tmp $REL_INV_CONFIG $KDE_dir/accuracy_estimations $KDE_dir/KDE_scoring

LOWEST_THRESHOLD_LIST="0.0 0.05 0.1 0.15 0.2 0.25 0.3 0.35 0.4"
for t in ${LOWEST_THRESHOLD_LIST}; do
    echo "python $TH_RELEX_ROOT/bin/tac-evaluation/eval-scripts/tune_threshold_2012-2015.py $scoring_output_all_years $init_params ${output_params}_t$t $NUM_ITER $REL_INV_CONFIG $t | tee ${PERFORMANCE_LOG}_t$t"
    python $TH_RELEX_ROOT/bin/tac-evaluation/eval-scripts/tune_threshold_2012-2015.py $scoring_output_all_years $init_params ${output_params}_t$t $NUM_ITER $REL_INV_CONFIG $t | tee ${PERFORMANCE_LOG}_t$t
    INIT_RECALL=`tail -n 1 ${PERFORMANCE_LOG}_t$t`
    echo "python $TH_RELEX_ROOT/bin/tac-evaluation/eval-scripts/tune_threshold_2012-2015.py $KDE_dir/KDE_scoring ${output_params}_t$t ${KDE_output_params}_t$t $NUM_ITER $REL_INV_CONFIG $t $INIT_RECALL | tee $KDE_dir/training_loss_log_t$t"
    python $TH_RELEX_ROOT/bin/tac-evaluation/eval-scripts/tune_threshold_2012-2015.py $KDE_dir/KDE_scoring ${output_params}_t$t ${KDE_output_params}_t$t $NUM_ITER $REL_INV_CONFIG $t $INIT_RECALL | tee $KDE_dir/training_loss_log_t$t
done

rm $scored_candidates_dir/inverses_with_tabs.tmp
