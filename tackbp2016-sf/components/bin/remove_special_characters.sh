#!/bin/bash

in_file=$1
out_file=$2

#TEMP_FILE=${out_file}_inter

cat $in_file | iconv -c -f UTF-8 -t ASCII \
| awk -F$'\t' 'BEGIN{OFS = FS} {sf_check=1} NF>=5{sf_check=$5; gsub(/ /,"",sf_check)} sf_check!=""{print $0} ' > $out_file

#> $TEMP_FILE

#rm $TEMP_FILE
