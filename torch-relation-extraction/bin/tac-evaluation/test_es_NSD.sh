#!/bin/bash

#sbatch --ntasks=15 --ntasks-per-node=3 --nodes=5 --cpus-per-task=1 --mem-per-cpu=30G ./bin/tac-evaluation/test_all_NSD.sh

folder=$1
INPUT_DIR=/iesl/canvas/hschang/TAC_2016/codes/torch-relation-extraction/results/${folder}

#years=(2012 2013 2014)
#years=(2013 2014)
#years=(es-test)
for file_path in $INPUT_DIR/*; do
    #for year in "${years[@]}"; do
        #dir_name=`dirname $file_path`
    srun --ntasks=1 --nodes=1 --exclusive -p cpu ${TH_RELEX_ROOT}/bin/tac-evaluation/score-tuned_NSD.sh es-test $file_path/es-test_scored $file_path/es-train/params $file_path/es-test_spa_2012 &
    awk '{print $1,0.7*$2}' $file_path/es-all/params > $file_path/es-all/params_07
    srun --ntasks=1 --nodes=1 --exclusive -p cpu ${TH_RELEX_ROOT}/bin/tac-evaluation/score-tuned_NSD.sh es-2016 $file_path/es-2016_scored $file_path/es-all/params_07 $file_path/es_2016_spa &
    srun --ntasks=1 --nodes=1 --exclusive -p cpu ${TH_RELEX_ROOT}/bin/tac-evaluation/score-tuned_NSD.sh es-2016-pilot $file_path/es-2016-pilot_scored $file_path/es-all/params_07 $file_path/es_2016_pilot_spa &
    #awk '{print $1,0.7*$2}' $file_path/es-train/params > $file_path/es-train/params_07
    #srun --ntasks=1 --nodes=1 --exclusive -p cpu ${TH_RELEX_ROOT}/bin/tac-evaluation/score-tuned_NSD.sh es-2016 $file_path/es_2016_scored $file_path/es-train/params_07 $file_path/es_2016_spa &
    #srun --ntasks=1 --nodes=1 --exclusive -p cpu ${TH_RELEX_ROOT}/bin/tac-evaluation/score-tuned_NSD.sh es-2016-pilot $file_path/es_2016_pilot_scored $file_path/es-train/params_07 $file_path/es_2016_pilot_spa &
    #done
done
wait
