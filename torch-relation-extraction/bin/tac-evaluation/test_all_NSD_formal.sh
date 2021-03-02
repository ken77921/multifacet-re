#!/bin/bash

TASK_NUM=15
NODE_NUM=5
TASK_PER_NODE_NUM=3

folder=$1
name=$2
export TEMP_FOLDER=`pwd`/tmp
mkdir -p $TEMP_FOLDER

sbatch --ntasks=$TASK_NUM --ntasks-per-node=$TASK_PER_NODE_NUM --nodes=$NODE_NUM --cpus-per-task=1 --mem-per-cpu=30G -J ${name}_test_all_NSD_formal ./bin/tac-evaluation/tune_2012_NSD.sh $folder
sbatch --ntasks=$TASK_NUM --ntasks-per-node=$TASK_PER_NODE_NUM --nodes=$NODE_NUM --cpus-per-task=1 --mem-per-cpu=30G -J ${name}_test_all_NSD_formal --dependency=singleton  ./bin/tac-evaluation/test_2013_2014_NSD.sh $folder
