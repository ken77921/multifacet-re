#!/bin/bash

input_file=$1
docs_list=$2
queries=$3
hop2_queries_expanded=$4
assessments=$5
hop1_response=$6
output_file=$7

export TAC_CONFIG=$TAC_ROOT/config/coldstart2015_UMass_IESL1.config


echo "$TAC_ROOT/components/bin/postprocess2015.sh $input_file $hop2_queries_expanded /dev/null ${input_file}_pp15"
$TAC_ROOT/components/bin/postprocess2015.sh $input_file $hop2_queries_expanded /dev/null ${input_file}_pp15

$TAC_ROOT/components/bin/response_cs_sf.sh ${input_file}_pp15 ${input_file}_noNIL

#$TAC_ROOT/components/bin/package_kb2015.sh $queries $hop1_response ${input_file}_noNIL ${input_file}_hop12

echo "/opt/perl/bin/perl5.14.2 -I $TAC_ROOT/evaluation/bin/2016_04 $TAC_ROOT/evaluation/bin/2016_04/CS-PackageOutput-MASTER.pl -docs $docs_list $queries $hop1_response ${input_file}_noNIL ${input_file}_hop12"
/opt/perl/bin/perl5.14.2 -I $TAC_ROOT/evaluation/bin/2016_04 $TAC_ROOT/evaluation/bin/2016_04/CS-PackageOutput-MASTER.pl -docs $docs_list $queries $hop1_response ${input_file}_noNIL ${input_file}_hop12

eval_perl_script=" -I $TAC_ROOT/evaluation/bin/2016_04 $TAC_ROOT/evaluation/bin/2016_04/CS-ValidateSF-MASTER.pl"

echo "/opt/perl/bin/perl5.14.2 $eval_perl_script -docs $docs_list -output_file ${input_file}_valid $queries ${input_file}_hop12"
/opt/perl/bin/perl5.14.2 $eval_perl_script -docs $docs_list -output_file ${input_file}_valid $queries ${input_file}_hop12


queries_eval=$TAC_ROOT/evaluation/resources/2015/batch_00_05_queryids.v3.0.txt

eval_perl_script=" -I $TAC_ROOT/evaluation/bin/2016_04/ $TAC_ROOT/evaluation/bin/2016_04/CS-Score-MASTER.pl"

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
