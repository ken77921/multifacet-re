#!/usr/bin/env bash

SCORED_CANDIDATE=$1
TUNED_PARAMS=$2
OUT=$3


#export TAC_ROOT=/iesl/canvas/belanger/relationfactory
#TMP_DIR=`mktemp -d`/out/run2013
#mkdir -p $TMP_DIR
#cd $TMP_DIR/../..
#echo working in $PWD

# get top k patterns

TMPDIR=/iesl/canvas/hschang/temp

SORTED_PREDICTION=`mktemp -p $TMPDIR`
sort -T /iesl/canvas/hschang/temp -t$'\t' -k7 -nr $SCORED_CANDIDATE > $SORTED_PREDICTION

>$OUT

# read in tuned params
while IFS='' read -r line || [[ -n "$line" ]]; do
  REL=`echo $line | cut -d' ' -f 1`
  t=`echo $line | cut -d' ' -f 2`
  echo "Getting scores with threshold $t for $REL"
  awk -v threshold=$t -F '\t' '{if($7 >= threshold) print  }' $SORTED_PREDICTION | grep $REL >> $OUT
done < "$TUNED_PARAMS"

echo computing performance for $OUT
