#!/bin/bash
query_xml=$1
resolved_queries=$2
assessments=$3
eval=$4
year=$5
queries_eval=$TAC_ROOT/evaluation/resources/2015/batch_00_05_queryids.v3.0.txt

case $year in
    "14")
        eval_perl_script=$TAC_ROOT/evaluation/bin/CS-Score.pl 
        ;;
    "15")
        eval_perl_script=" -I $TAC_ROOT/evaluation/bin/2015/ $TAC_ROOT/evaluation/bin/2015/CS-Score-MASTER.pl"
        ;;
    *)
        echo "year should be 14 or 15"
        exit 1
        ;;
esac


echo "/opt/perl/bin/perl5.14.2 $eval_perl_script \
-discipline STRING_CASE \
-output_file $eval \
-queries $queries_eval \
$query_xml $resolved_queries $assessments"

/opt/perl/bin/perl5.14.2 $eval_perl_script \
-discipline STRING_CASE \
-output_file $eval \
-queries $queries_eval \
$query_xml $resolved_queries $assessments
