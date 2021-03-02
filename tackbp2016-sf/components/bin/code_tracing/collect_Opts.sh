#!/bin/bash
#find ./src -type f -print0 | xargs -0 -I % sh -c "echo %" > Code_opt_all
#find ./src -type f -print0 | xargs -0 -I % sh -c "echo %; sed -n -e '/extends DefaultCmdOptions/,/}/ p %'" > Code_opt_all
output_file=./Code_opt_all

printf "Scripts run line\n" > "$output_file"
grep "run.sh" ../../bin/* >> "$output_file"

printf "\narguments in java codes\n" >> "$output_file"
find ../../pipeline/src -type f -print0 | xargs -0 -I % sh -c "echo %;grep -n 'args\['  %" >> "$output_file"
echo "output to $output_file"
