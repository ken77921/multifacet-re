#!/bin/bash

TASK_NUM=10
NODE_NUM=2
TASK_PER_NODE_NUM=5

folder=$1
name=$2

sbatch --ntasks=$TASK_NUM --ntasks-per-node=$TASK_PER_NODE_NUM --nodes=$NODE_NUM --cpus-per-task=1 --mem-per-cpu=30G -J ${name}_test_all_NSD_es ./bin/tac-evaluation/tune_es_NSD.sh $folder
sbatch --ntasks=$TASK_NUM --ntasks-per-node=$TASK_PER_NODE_NUM --nodes=$NODE_NUM --cpus-per-task=1 --mem-per-cpu=30G -J ${name}_test_all_NSD_es --dependency=singleton  ./bin/tac-evaluation/test_es_NSD.sh $folder
