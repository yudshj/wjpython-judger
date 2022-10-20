#!/bin/bash

#./gen_tar.sh 18506

name="result"
files=""
args=("$@")
for i in $args
do
    python3 ./judger.py $i
    files="$files playground/${i}_copied_code ${i}_result.csv"
    name="$name-$i"
done

tar cvzf ${name}.tar.gz $files
