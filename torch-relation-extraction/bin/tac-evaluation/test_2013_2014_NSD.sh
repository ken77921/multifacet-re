#!/bin/bash

#sbatch --ntasks=15 --ntasks-per-node=3 --nodes=5 --cpus-per-task=1 --mem-per-cpu=30G ./bin/tac-evaluation/test_all_NSD.sh

folder=$1
INPUT_DIR=/iesl/canvas/hschang/TAC_2016/codes/torch-relation-extraction/results/${folder}

#years=(2012 2013 2014)
years=(2013 2014)
for file_path in $INPUT_DIR/*; do
    for year in "${years[@]}"; do
        #dir_name=`dirname $file_path`
        srun --ntasks=1 --nodes=1 --exclusive -p cpu ${TH_RELEX_ROOT}/bin/tac-evaluation/score-tuned_NSD.sh $year $file_path/${year}_scored $file_path/2012/params $file_path/${year}_formal &
    done
done
wait
