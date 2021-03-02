#!/bin/bash
set -e


#cat $1 | grep -v NIL > $2

cat $1 \
 | grep -v $'\t'"NIL$" | grep -v $'\t'"NIL"$'\t' \
 | sed '/\&amp;/! s/\&/\&amp;/g' \
 | tr -d '#' > $2

#cat $1 \
# | grep -v NIL \
# | sed '/\&amp;/! s/\&/\&amp;/g' \
# | tr -d '#' > $2

#cat $1 \
# | grep -v NIL \
# | sed '/\&amp;/! s/\&/\&amp;/g' \
# | tr -d '#' \
# | iconv -c -f UTF-8 -t ASCII > $2

