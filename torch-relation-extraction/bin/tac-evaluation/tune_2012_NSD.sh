#!/bin/bash

#sbatch --ntasks=15 --ntasks-per-node=3 --nodes=5 --cpus-per-task=1 --mem-per-cpu=30G ./bin/tac-evaluation/test_all_NSD.sh

folder=$1
INPUT_DIR=/iesl/canvas/hschang/TAC_2016/codes/torch-relation-extraction/results/${folder}

#test_years=(2012 2013 2014)
for file_path in $INPUT_DIR/*; do
    srun --ntasks=1 --nodes=1 --exclusive -p cpu ${TH_RELEX_ROOT}/bin/tac-evaluation/tune-thresh-prescored.sh 2012 $file_path/2012_scored $file_path/2012 &
    #for year in "${years[@]}"; do
    #    #dir_name=`dirname $file_path`
    #done
done
wait
