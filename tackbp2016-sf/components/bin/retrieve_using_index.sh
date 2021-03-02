#!/bin/sh
index=$2

NUM_DOCS=`$TAC_ROOT/bin/get_config.sh num_retrieve 500`
STRICT=`$TAC_ROOT/bin/get_config.sh strict_retrieval false`
STOP_LIST=`$TAC_ROOT/bin/get_config.sh stop_words_list /iesl/canvas/proj/tackbp/2016-pilot/stop_words_en_es`

echo "Using stop word file: $STOP_LIST"

echo "Retrieving max. $NUM_DOCS documents per query."

$TAC_ROOT/components/bin/run.sh run.Retrieve $1 $index $NUM_DOCS $3 $STOP_LIST  $STRICT
