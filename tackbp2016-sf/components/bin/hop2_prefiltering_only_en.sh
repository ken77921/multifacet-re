#!/bin/bash

IN=$1  
THRESHOLD=/iesl/canvas/hschang/TAC_2016/codes/torch-relation-extraction/results/hop2_params/hop1_params_org_min
OUTPUT=$2

/iesl/canvas/hschang/TAC_2016/codes/torch-relation-extraction/bin/tac-evaluation/eval-scripts/threshold-scored-candidates_7.sh $IN $THRESHOLD ${OUTPUT}.tmp

awk '$4 ~ /ENG_/ { print $0 }' ${OUTPUT}.tmp > ${OUTPUT}
#python $TAC_ROOT/components/simple_scripts/keep_only_en_source.py ${OUTPUT}.tmp $OUTPUT

rm ${OUTPUT}.tmp
