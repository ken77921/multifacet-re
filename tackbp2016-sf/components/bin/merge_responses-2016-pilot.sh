#!/bin/sh
# merge_responses-2016-pilot.sh <runid> <query_expanded_xml> <response>*
# a response is written to stdout

runid=$1

# MergeResponses <query_expanded_xml> <teamid> <response>*
$TAC_ROOT/components/bin/run.sh run.MergeResponses $2 $runid ${@:3}
