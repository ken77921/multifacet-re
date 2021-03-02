#!/bin/sh
# Response <query_expanded_xml> <prediction> <team_id>
# a response is written to stdout

runid=`$TAC_ROOT/bin/get_config.sh runid UMass_IESL`
#rel2inv_mapping_file="/iesl/canvas/hschang/TAC_2016/codes/tackbp2016-kb/config/coldstart_relations2015_inverses.config"

echo "$TAC_ROOT/components/bin/run.sh run.PredictionToResponse_inv $1 $2 $runid  > $3"
$TAC_ROOT/components/bin/run.sh run.PredictionToResponse_inv $1 $2 $runid  > $3
#echo "$TAC_ROOT/components/bin/run.sh run.PredictionToResponse_inv $1 $2 $runid $rel2inv_mapping_file > $3"
#$TAC_ROOT/components/bin/run.sh run.PredictionToResponse_inv $1 $2 $runid $rel2inv_mapping_file > $3
