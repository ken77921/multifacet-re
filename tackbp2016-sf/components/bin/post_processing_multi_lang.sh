#!/bin/bash

input_dir=$1
docs_list=$2
queries=$3
queries_expanded=$4
output_file=$5
config_file=$6
input_files_list=${@:7}

export TAC_ROOT=/iesl/canvas/hschang/TAC_2016/codes/tackbp2016-sf
#export TAC_CONFIG=$TAC_ROOT/config/coldstart2016pilot_spa_UMass_IESL2.config
export TAC_CONFIG=$config_file

mkdir -p $input_dir
input_file=$input_dir/response_XLING

echo "$TAC_ROOT/components/bin/merge_responses.sh $queries_expanded $input_files_list > $input_file"
$TAC_ROOT/components/bin/merge_responses.sh $queries_expanded $input_files_list > $input_file

echo "$TAC_ROOT/components/bin/postprocess2016_en_es.sh $input_file $queries_expanded /dev/null ${input_file}_pp15"
$TAC_ROOT/components/bin/postprocess2016_en_es.sh $input_file $queries_expanded /dev/null ${input_file}_pp15

$TAC_ROOT/components/bin/response_cs_sf.sh ${input_file}_pp15 ${input_file}_noNIL

eval_perl_script=" -I $TAC_ROOT/evaluation/bin/2016_04 $TAC_ROOT/evaluation/bin/2016_04/CS-ValidateSF-MASTER.pl"

echo "/opt/perl/bin/perl5.14.2 $eval_perl_script -docs $docs_list -output_file ${input_file}_valid $queries ${input_file}_noNIL"

/opt/perl/bin/perl5.14.2 $eval_perl_script -docs $docs_list -output_file ${output_file} $queries ${input_file}_noNIL

