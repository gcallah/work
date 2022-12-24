#!/bin/sh

# clear out old work:
echo "\n" > tmp/abstracts.md

declare -a chap_list=$(cat structure/chap_order.txt)

for chap in ${chap_list[@]}
do
    cat abstracts/$chap.md >> tmp/abstracts.md
    # make sure there's always a newline between chaps:
    echo "\n" >> tmp/abstracts.md
done
