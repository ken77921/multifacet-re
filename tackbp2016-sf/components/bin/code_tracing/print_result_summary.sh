#!/bin/bash

if [ $# -ne 1 ]; then
    echo "./print_result_summary run_dir"
    exit 1
fi

run_dir=$1
out_file=./result_summary.txt

> $out_file
function output_files()
{
    echo "$1" >> $out_file
    if [[ -f "$1" ]]; then
        head -n 10 "$1" | cut -c -160 >> $out_file
    fi
    echo -e "\n" >> $out_file
}

for file in "$run_dir"/*
do
    if [[ -d $file ]]; then
        for file_d in "$file"/*
        do
            output_files $file_d
            echo -e "\n" >> $out_file
        done
    elif [[ -f $file ]]; then
        output_files $file
    fi
done

echo "Output to $out_file"
