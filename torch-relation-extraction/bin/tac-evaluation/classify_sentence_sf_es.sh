#!/usr/bin/env bash

CANDIDATES=$1
QUERY_EXPANDED=$2
OUT=$3
GPU=$4

TAC_EVAL_ROOT=${TH_RELEX_ROOT}/bin/tac-evaluation

#MODEL_USchema=${TH_RELEX_ROOT}/models/uschema-english-relogged-100d_more_data/2016-07-31_13/15-model
#MODEL_USchema=${TH_RELEX_ROOT}/models/uschema-english-relogged-100d_es_en_org_full/2016-08-13_19/15-model
MODEL_USchema=${TH_RELEX_ROOT}/models/uschema-english-relogged-100d_es_en_org/2016-08-12_23/15-model
#VOCAB_USchema=/iesl/canvas/hschang/TAC_2016/codes/torch-relation-extraction/data/train_processed_files/Ben_for_USchema_more_data_baseline_training/training_vocab-relations.txt
#VOCAB_USchema=${TH_RELEX_ROOT}/data/train_processed_files/en_es_org_full_log_training/training_vocab-relations.txt
VOCAB_USchema=${TH_RELEX_ROOT}/data/train_processed_files/en_es_org_log_training/training_vocab-relations.txt
#TUNED_PARAMS_USchema=${TH_RELEX_ROOT}/results/USchema_100d_more_data_baseline_15/2014_tune/params
#TUNED_PARAMS_USchema=${TH_RELEX_ROOT}/results/USchema_100d_more_data_baseline_15/2015_tune/params
#TUNED_PARAMS_USchema=${TH_RELEX_ROOT}/results/USchema_100d_more_data_baseline_15/2012-2015_tune/params
#TUNED_PARAMS_USchema=${TH_RELEX_ROOT}/results/USchema_100d_more_data_baseline_15/KDE_tune/params_t0.25
#TUNED_PARAMS_USchema=${TH_RELEX_ROOT}/results/USchema_100d_es_en_org_full_all_tuned_t035/es-all/params
TUNED_PARAMS_USchema=${TH_RELEX_ROOT}/results/USchema_100d_es_en_org_all_tuned_t025/es-all/params_07
#TUNED_PARAMS_USchema=${TH_RELEX_ROOT}/results/USchema_100d_es_en_org_all_tuned_t01/es-all/params
OUT_USchema=${OUT}/USchema

#MODEL_LSTM=${TH_RELEX_ROOT}/models/lstm-bi-maxpool-paper_USchema_init_more_data_normal/2016-08-01_20/9-model
#MODEL_LSTM=${TH_RELEX_ROOT}/models/lstm-bi-maxpool-paper_USchema_init_more_data_sdrop_aug/2016-08-10_01/15-model
MODEL_LSTM=${TH_RELEX_ROOT}/models/lstm-bi-maxpool-paper_USchema_init_weighted_es_en_org/2016-08-13_09/15-model
#VOCAB_LSTM=/iesl/canvas/hschang/TAC_2016/codes/torch-relation-extraction/data/train_processed_files/Ben_more_data_baseline_aug_training/training_vocab-tokens.txt
VOCAB_LSTM=${TH_RELEX_ROOT}/data/train_processed_files/en_es_org_translated_training/training_vocab-tokens.txt
#MODEL_LSTM=${TH_RELEX_ROOT}/models/lstm-bi-maxpool-paper_USchema_init_more_data_sdrop/2016-08-05_12/15-model
#VOCAB_LSTM=/iesl/canvas/hschang/TAC_2016/codes/torch-relation-extraction/data/train_processed_files/Ben_more_data_baseline_normal_training/training_vocab-tokens.txt
#TUNED_PARAMS_LSTM=${TH_RELEX_ROOT}/results/LSTM_USchema_org_more_data_normal_max_seq_9/2014_tune/params
#TUNED_PARAMS_LSTM=${TH_RELEX_ROOT}/results/LSTM_USchema_org_more_data_sdrop_15/2014_tune/params
#TUNED_PARAMS_LSTM=${TH_RELEX_ROOT}/results/LSTM_USchema_org_more_data_sdrop_15/2015_tune/params
#TUNED_PARAMS_LSTM=${TH_RELEX_ROOT}/results/LSTM_USchema_org_more_data_sdrop_15/2012-2015_tune/params
#TUNED_PARAMS_LSTM=${TH_RELEX_ROOT}/results/LSTM_USchema_org_more_data_sdrop_aug_15/2012-2015_tune/params
#TUNED_PARAMS_LSTM=${TH_RELEX_ROOT}/results/LSTM_USchema_org_es_en_org_translated_t035_15/es-all/params
TUNED_PARAMS_LSTM=${TH_RELEX_ROOT}/results/LSTM_USchema_org_es_en_org_translated_all_tuned_t025_15/es-all/params_07
#TUNED_PARAMS_LSTM=${TH_RELEX_ROOT}/results/LSTM_USchema_org_es_en_org_translated_all_tuned_t01_15/es-all/params
OUT_LSTM=${OUT}/LSTM

MAX_SEQ=20

${TH_RELEX_ROOT}/bin/tac-evaluation/score-tuned_for_sf_pipeline.sh $CANDIDATES $QUERY_EXPANDED $MODEL_USchema $VOCAB_USchema $GPU $MAX_SEQ $TUNED_PARAMS_USchema $OUT_USchema -logRelations -relations

DICT_LOC=/home/pat/canvas/torch-relation-extraction/vocabs/en_es.dictionary.uniq

${TH_RELEX_ROOT}/bin/tac-evaluation/score-tuned_for_sf_pipeline.sh $CANDIDATES $QUERY_EXPANDED $MODEL_LSTM $VOCAB_LSTM $GPU $MAX_SEQ $TUNED_PARAMS_LSTM $OUT_LSTM -dictionary $DICT_LOC
mkdir -p ${OUT}

RESPONSE="${OUT}/response"

cat ${OUT_LSTM}/response ${OUT_USchema}/response > $RESPONSE
