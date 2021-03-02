#!/bin/bash

year=$1
vocab=$2
model=$3
gpu=$4
scored_candidates_dir=$5/$year
scoring_output_all_years=$5/scoring_output
MAX_SEQ=$6
eval_args=${@:7}

TAC_EVAL_ROOT=${TH_RELEX_ROOT}/bin/tac-evaluation
source ${TAC_EVAL_ROOT}/configs/${year}

mkdir -p $scored_candidates_dir

CAND_SCORE_CMD="th ${TH_RELEX_ROOT}/src/eval/ScoreCandidateFile.lua -candidates $CANDIDATES -vocabFile $vocab -model $model -gpuid $gpu -threshold 0 -outFile $scored_candidates_dir/scored_candidates -maxSeq $MAX_SEQ $eval_args"
echo $CAND_SCORE_CMD
$CAND_SCORE_CMD

echo "Post processing for year $year"
$TAC_ROOT/components/bin/response.sh $QUERY_EXPANDED $scored_candidates_dir/scored_candidates $scored_candidates_dir/response_full
if [[ $year == "2014" ]]; then
  $TAC_ROOT/components/bin/postprocess2014.sh $scored_candidates_dir/response_full $QUERY_EXPANDED /dev/null $scored_candidates_dir/response_full_pp
elif [[ $year == "2013" ]]; then
  $TAC_ROOT/components/bin/postprocess2013.sh $scored_candidates_dir/response_full $QUERY_EXPANDED /dev/null $scored_candidates_dir/response_full_pp
elif [[ $year == "2012" ]]; then
  COMP=$TAC_ROOT/components/pipeline/
  LINKSTAT=/dev/null
  JAVA_HOME=$TAC_ROOT/lib/java/jdk1.6.0_18/
  $TAC_ROOT/components/bin/run.sh run.RedundancyEliminator $LINKSTAT $scored_candidates_dir/response_full $QUERY_EXPANDED > $scored_candidates_dir/response_full_pp
else
  cp $scored_candidates_dir/response_full $scored_candidates_dir/response_full_pp
fi

$TAC_ROOT/components/bin/response_cs_sf.sh $scored_candidates_dir/response_full_pp $scored_candidates_dir/response_full_pp_noNIL


RELCONFIG=/iesl/canvas/beroth/workspace/relationfactory_iesl/config/relations_coldstart2015.config

python $TH_RELEX_ROOT/bin/tac-evaluation/eval-scripts/scoring_outputs_for_tuning_2012-2014.py $scored_candidates_dir/response_full_pp_noNIL $KEY $scored_candidates_dir/scoring_output $year

cat $scored_candidates_dir/scoring_output >> $scoring_output_all_years
