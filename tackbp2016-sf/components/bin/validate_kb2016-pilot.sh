#!/bin/bash
set -e

input_kb=$1
query=$2
output_kb=$3

export PERL5LIB="$TAC_ROOT/components/tac2016-pilot/ColdStart/"


if [ "$#" -lt 4 ]; then
    docs=`$TAC_ROOT/bin/get_expand_config.sh doclengths`
else
    docs=$4
fi


error_file=${output_kb}.errors

rm -f $output_kb $error_file

echo "/opt/perl/bin/perl5.14.2 $TAC_ROOT/components/tac2016-pilot/ColdStart/CS-ValidateSF-MASTER.pl \
 -docs $docs \
 -error_file $error_file \
 -output_file $output_kb \
 $query \
 $input_kb "


/opt/perl/bin/perl5.14.2 $TAC_ROOT/components/tac2016-pilot/ColdStart/CS-ValidateSF-MASTER.pl \
 -docs $docs \
 -error_file $error_file \
 -output_file $output_kb \
 $query \
 $input_kb

cat $error_file

