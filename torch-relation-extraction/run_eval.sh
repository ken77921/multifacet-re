#!/bin/bash

export TH_RELEX_ROOT=`pwd`
export TAC_ROOT=/iesl/canvas/hschang/TAC_2016/codes/tackbp2016-sf 
export LD_LIBRARY_PATH="/home/hschang/anaconda3/lib/:$LD_LIBRARY_PATH"

lang=$1

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
  if [[ "${lang}" == "en" ]]; then
      ./bin/tac-evaluation/test_all_NSD_formal.sh ${run}_${suffix}_results ${run}_${suffix}
  else
      ./bin/tac-evaluation/test_all_NSD_es.sh ${run}_${suffix}_results ${run}_${suffix}
  fi
done
