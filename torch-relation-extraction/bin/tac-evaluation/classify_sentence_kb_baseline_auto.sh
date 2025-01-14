#!/usr/bin/env bash

CANDIDATES=$1
OUT=$2
GPU=$3

TAC_EVAL_ROOT=${TH_RELEX_ROOT}/bin/tac-evaluation

MODEL_USchema=${TH_RELEX_ROOT}/models/uschema-english-relogged-100d_more_data/2016-07-31_13/15-model
VOCAB_USchema=/iesl/canvas/hschang/TAC_2016/codes/torch-relation-extraction/data/train_processed_files/Ben_for_USchema_more_data_baseline_training/training_vocab-relations.txt
#TUNED_PARAMS_USchema=${TH_RELEX_ROOT}/results/USchema_100d_more_data_baseline_15/2014_tune/params
#TUNED_PARAMS_USchema=${TH_RELEX_ROOT}/results/USchema_100d_more_data_baseline_15/2015_tune/params
TUNED_PARAMS_USchema=${TH_RELEX_ROOT}/results/USchema_100d_more_data_baseline_15/2012-2015_tune/params_t0.25
#TUNED_PARAMS_USchema=${TH_RELEX_ROOT}/results/USchema_100d_more_data_baseline_15/2012-2015_tune/params_t035
#TUNED_PARAMS_USchema=${TH_RELEX_ROOT}/results/USchema_100d_more_data_baseline_15/KDE_tune/params_t0.35
#TUNED_PARAMS_USchema=${TH_RELEX_ROOT}/results/USchema_100d_more_data_baseline_15/KDE_tune/params_t0.25_manually_tuned
#OUT_USchema=${TH_RELEX_ROOT}/results/USchema_100d_more_data_baseline_15/2015-kb
OUT_USchema=${OUT}/USchema_kb


#MODEL_LSTM=${TH_RELEX_ROOT}/models/lstm-bi-maxpool-paper_USchema_init_more_data_normal/2016-08-01_20/9-model
MODEL_LSTM=${TH_RELEX_ROOT}/models/lstm-bi-maxpool-paper_USchema_init_more_data_sdrop_aug/2016-08-10_01/15-model
VOCAB_LSTM=/iesl/canvas/hschang/TAC_2016/codes/torch-relation-extraction/data/train_processed_files/Ben_more_data_baseline_aug_training/training_vocab-tokens.txt
#MODEL_LSTM=${TH_RELEX_ROOT}/models/lstm-bi-maxpool-paper_USchema_init_more_data_sdrop/2016-08-05_12/15-model
#VOCAB_LSTM=/iesl/canvas/hschang/TAC_2016/codes/torch-relation-extraction/data/train_processed_files/Ben_more_data_baseline_normal_training/training_vocab-tokens.txt
#TUNED_PARAMS_LSTM=${TH_RELEX_ROOT}/results/LSTM_USchema_org_more_data_normal_max_seq_9/2014_tune/params
#TUNED_PARAMS_LSTM=${TH_RELEX_ROOT}/results/LSTM_USchema_org_more_data_sdrop_15/2014_tune/params
#TUNED_PARAMS_LSTM=${TH_RELEX_ROOT}/results/LSTM_USchema_org_more_data_sdrop_15/2015_tune/params
TUNED_PARAMS_LSTM=${TH_RELEX_ROOT}/results/LSTM_USchema_org_more_data_sdrop_15/2012-2015_tune/params_t0.25
#TUNED_PARAMS_LSTM=${TH_RELEX_ROOT}/results/LSTM_USchema_org_more_data_sdrop_15/2012-2015_tune/params_t035
#TUNED_PARAMS_LSTM=${TH_RELEX_ROOT}/results/LSTM_USchema_org_more_data_sdrop_aug_15/2012-2015_tune/params_t035
#TUNED_PARAMS_LSTM=${TH_RELEX_ROOT}/results/LSTM_USchema_org_more_data_sdrop_aug_15/KDE_tune/params_t0.35
#TUNED_PARAMS_LSTM=${TH_RELEX_ROOT}/results/LSTM_USchema_org_more_data_sdrop_aug_15/KDE_tune/params_t0.25_manual_tuned

#OUT_LSTM=${TH_RELEX_ROOT}/results/LSTM_USchema_org_more_data_normal_max_seq_9/2015-kb
OUT_LSTM=${OUT}/LSTM_kb

MAX_SEQ=20

${TH_RELEX_ROOT}/bin/tac-evaluation/score-tuned_for_kb_pipeline.sh $CANDIDATES $MODEL_USchema $VOCAB_USchema $GPU $MAX_SEQ $TUNED_PARAMS_USchema $OUT_USchema -logRelations -relations

${TH_RELEX_ROOT}/bin/tac-evaluation/score-tuned_for_kb_pipeline.sh $CANDIDATES $MODEL_LSTM $VOCAB_LSTM $GPU $MAX_SEQ $TUNED_PARAMS_LSTM $OUT_LSTM

mkdir -p ${OUT}

THRESHOLD_CANDIDATE="${OUT}/threshold_candidate"

cat ${OUT_LSTM}/threshold_candidate ${OUT_USchema}/threshold_candidate > $THRESHOLD_CANDIDATE
