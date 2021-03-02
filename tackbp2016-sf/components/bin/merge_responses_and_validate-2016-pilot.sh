#!/bin/bash

runid=$1
QUERIES_EXPANDED=$2
output=$3
responses=${@:4}

RESPONSE="$output".merged
sh $TAC_ROOT/components/bin/merge_responses-2016-pilot.sh $runid $QUERIES_EXPANDED $responses > $RESPONSE

# Post process
RESPONSE_PP="$RESPONSE".pp15
$TAC_ROOT/components/bin/postprocess2015.sh $RESPONSE $QUERIES_EXPANDED /dev/null $RESPONSE_PP

# Remove nils and escape special characters
RESPONSE_NO_NILS="$RESPONSE_PP".noNILS
sh $TAC_ROOT/components/bin/response_cs_sf.sh $RESPONSE_PP $RESPONSE_NO_NILS

# Run validation script
RESPONSE_VALID="$RESPONSE_NO_NILS".valid
queries_validation=/iesl/canvas/nmonath/tac/2016/tackbp2016-sf/runs/coldstart2016_pilot_eng_UMass_IESL1/query.xml
doclengths_validation=/iesl/canvas/proj/tackbp/2016-pilot/tac_2016_kbp_spanish_slot_filling_pilot_evaluation_source_corpus.doclengths.txt
sh $TAC_ROOT/components/bin/validate_kb2016-pilot.sh $RESPONSE_NO_NILS  $queries_validation $RESPONSE_VALID $doclengths_validation


