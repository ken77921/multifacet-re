#!/bin/bash

#folder=$1
#INPUT_DIR=${TH_RELEX_ROOT}/results/${folder}
INPUT_DIR=$1

for file_path in $INPUT_DIR/*; do
    ${TH_RELEX_ROOT}/bin/tac-evaluation/tune-thresh-prescored.sh 2012 $file_path/2012_scored $file_path/2012
done
wait
