#!/bin/bash

cmds=("$@")

echo "${#cmds[@]}"
for (( i=0; i < ${#cmds[@]}; i++)); do
  echo "${cmds[$i]}"
  eval "${cmds[$i]}"
done
