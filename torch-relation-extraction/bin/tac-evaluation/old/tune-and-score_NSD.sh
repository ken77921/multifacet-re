#!/bin/bash

TUNE_YEAR=$1
TEST_YEAR=$2
SCORED_FILE_TUNE=$3
SCORED_FILE_TEST=$4
OUT=$5

# tune thresholds
${TH_RELEX_ROOT}/bin/tac-evaluation/tune-thresh-prescored.sh $TUNE_YEAR $SCORED_FILE_TUNE $OUT/$TUNE_YEAR

# use tuned thresholds and evaluate on test year
${TH_RELEX_ROOT}/bin/tac-evaluation/score-tuned_NSD.sh $TEST_YEAR $SCORED_FILE_TEST $OUT/$TUNE_YEAR/params $OUT/$TEST_YEAR
