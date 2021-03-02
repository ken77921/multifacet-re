#!/bin/bash

input_file=$1
docs_list=$2
queries=$3
output_file=$4
year=$5

case $year in
    "14")
        eval_perl_script=$TAC_ROOT/evaluation/bin/CS-ValidateSF.pl 
        ;;
    "15")
        eval_perl_script=" -I $TAC_ROOT/evaluation/bin/2015 $TAC_ROOT/evaluation/bin/2015/CS-ValidateSF-MASTER.pl"
        ;;
    *)
        echo "year should be 14 or 15"
        exit 1
        ;;
esac

echo "/opt/perl/bin/perl5.14.2 $eval_perl_script -docs $docs_list -output_file $output_file $queries $input_file"

/opt/perl/bin/perl5.14.2 $eval_perl_script -docs $docs_list -output_file $output_file $queries $input_file
