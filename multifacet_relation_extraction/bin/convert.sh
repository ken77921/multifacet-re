#!/bin/bash


RUN_OUTPUTS=(
milestone_run_trans-b5-kb11
)

for run in "${RUN_OUTPUTS[@]}"; do
  if [[ "${run}" == *"lstm"* && "${run}" == *"trans"* ]]; then
    suffix="lstm_trans"
  elif [[ "${run}" == *"lstm"* ]]; then
    suffix="lstm"
  else
    suffix="trans"
  fi
  $PY_PATH src/testing/convert_all_scores.py ${run} ${run}_${suffix}_results ${suffix} &
  done

wait
