#!/bin/bash
response=$1
key=$2

TMPDIR=/iesl/canvas/hschang/temp
java -Djava.io.tmpdir=$TMPDIR -cp ${TH_RELEX_ROOT}/bin/tac-evaluation/eval-scripts/SFScore-2016 SFScore $response $key  nocase anydoc  | grep -P '\tRecall:|\tPrecision:|\tF1:'
