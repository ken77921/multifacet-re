#!/bin/bash

input_file=$1
docs_list=$2
queries=$3
queries_expanded=$4
assessments=$5
output_file=$6

export TAC_CONFIG=$TAC_ROOT/config/coldstart2015_UMass_IESL1.config


echo "$TAC_ROOT/components/bin/postprocess2015.sh $input_file $queries_expanded /dev/null ${input_file}_pp15"
$TAC_ROOT/components/bin/postprocess2015.sh $input_file $queries_expanded /dev/null ${input_file}_pp15

$TAC_ROOT/components/bin/response_cs_sf.sh ${input_file}_pp15 ${input_file}_noNIL

eval_perl_script=" -I $TAC_ROOT/evaluation/bin/2015 $TAC_ROOT/evaluation/bin/2015/CS-ValidateSF-MASTER.pl"

echo "/opt/perl/bin/perl5.14.2 $eval_perl_script -docs $docs_list -output_file ${input_file}_valid $queries ${input_file}_noNIL"

/opt/perl/bin/perl5.14.2 $eval_perl_script -docs $docs_list -output_file ${input_file}_valid $queries ${input_file}_noNIL

queries_eval=$TAC_ROOT/evaluation/resources/2015/batch_00_05_queryids.v3.0.txt

eval_perl_script=" -I $TAC_ROOT/evaluation/bin/2015/ $TAC_ROOT/evaluation/bin/2015/CS-Score-MASTER.pl"

echo "/opt/perl/bin/perl5.14.2 $eval_perl_script \
-discipline STRING_CASE \
-output_file $output_file \
-queries $queries_eval \
$queries ${input_file}_valid $assessments"

/opt/perl/bin/perl5.14.2 $eval_perl_script \
-discipline STRING_CASE \
-output_file $output_file \
-queries $queries_eval \
$queries ${input_file}_valid $assessments
