#!/bin/bash

#folder=$1
INPUT_DIR=$1
mkdir -p `pwd`/tmp
export TEMP_FOLDER=`pwd`/tmp

for file_path in $INPUT_DIR/*; do
    ${TH_RELEX_ROOT}/bin/tac-evaluation/tune-thresh-prescored.sh 2012 $file_path/2012_scored $file_path/2012 $TEMP_FOLDER
done

years=(2013 2014)
for file_path in $INPUT_DIR/*; do
    for year in "${years[@]}"; do
        ${TH_RELEX_ROOT}/bin/tac-evaluation/score-tuned_NSD.sh $year $file_path/${year}_scored $file_path/2012/params $file_path/${year}_formal
    done
done
rm -rf $TEMP_FOLDER
unset TEMP_FOLDER
