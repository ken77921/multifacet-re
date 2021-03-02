#!/bin/bash
#
# Run the Factorie slotfilling tagger pipeline on RelationFactory input/output
#   Usage: rf-tagger-wrapper.sh inputFile outputFile

input=$1
output=$2
# hack to deal with multiple tac roots
# set tac_2015_root to the tackbp2015 project
#TAC_2015_ROOT=/iesl/canvas/ajaynagesh/tac2016/tackbp2016-kb/
TAC_2015_ROOT=/iesl/canvas/hschang/TAC_2016/codes/tackbp2016-kb
TMP_TAC_ROOT=$TAC_ROOT
TAC_ROOT=$TAC_2015_ROOT

echo "In the es-tagging.sh component"

$TAC_ROOT/bin/run_class.sh edu.umass.cs.iesl.tackbp2015.process.SpanishRelationFactoryWrapper \
--input-file=$input \
--output-file=$output

TAC_ROOT=$TMP_TAC_ROOT
