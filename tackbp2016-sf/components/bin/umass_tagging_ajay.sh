#!/bin/bash 
# Tags sentences in drank format.

#TAC_ROOT=/iesl/canvas/beroth/synced/tackbp2015/ /iesl/canvas/beroth/synced/tackbp2015/bin/wrappers/rf-tagger-wrapper.sh $1 $2.tmp
#TAC_ROOT=/iesl/canvas/beroth/workspace/tackbp2015/ /iesl/canvas/beroth/workspace/tackbp2015/bin/wrappers/rf-tagger-wrapper.sh $1 $2.tmp
#TAC_ROOT=/iesl/canvas/hschang/TAC_2016/codes/tackbp2016-kb /iesl/canvas/hschang/TAC_2016/codes/tackbp2016-kb/bin/wrappers/rf-tagger-wrapper.sh $1 $2.tmp
TAC_ROOT=/iesl/canvas/ajaynagesh/tackbp2016/aug/tackbp2016-kb /iesl/canvas/hschang/TAC_2016/codes/tackbp2016-kb/bin/wrappers/rf-tagger-wrapper.sh $1 $2.tmp

cat $2.tmp | sed 's# L-# I-#g' | sed 's# U-# B-#g' > $2

rm $2.tmp

