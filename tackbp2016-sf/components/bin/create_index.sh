#!/bin/bash
index=$1

corpusdatapath=`$TAC_ROOT/bin/get_expand_config.sh corpusdatapath`
docidlist=`$TAC_ROOT/bin/get_expand_config.sh docidlist`
STOP_LIST=`$TAC_ROOT/bin/get_config.sh stop_words_list /iesl/canvas/proj/tackbp/2016-pilot/stop_words_en_es`

echo "Using stop word file: $STOP_LIST" 

$TAC_ROOT/components/bin/run.sh indexir.Indexing $corpusdatapath COLDSTART2014 false $index $docidlist $STOP_LIST

echo "$TAC_ROOT/components/bin/run.sh indexir.IdFileMapping $index ${index}.idfile_mapping"

$TAC_ROOT/components/bin/run.sh indexir.IdFileMapping $index ${index}.idfile_mapping

