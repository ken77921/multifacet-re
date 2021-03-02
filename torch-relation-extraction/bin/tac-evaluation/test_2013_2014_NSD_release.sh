#!/bin/bash


folder=$1
INPUT_DIR=${TH_RELEX_ROOT}/results/${folder}

years=(2013 2014)
for file_path in $INPUT_DIR/*; do
    for year in "${years[@]}"; do
        ${TH_RELEX_ROOT}/bin/tac-evaluation/score-tuned_NSD.sh $year $file_path/${year}_scored $file_path/2012/params $file_path/${year}_formal
    done
done
wait
