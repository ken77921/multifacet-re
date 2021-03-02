#!/bin/bash

conf=$1
name=$2
partition=$3
other_args=${@:4}

if [[ -z "${partition}" ]]; then
  bash ./bin/run_gpu_code.sh $conf $name
else
  sbatch \
  --job-name=${name} \
  --output="logs/tr-${name}.txt" \
  --err="logs/tr-${name}.err" \
  --gres=gpu:1 \
  --partition=${partition} \
  --mem=40G \
  ${other_args} \
  bin/run_gpu_code.sh $conf $name
fi
