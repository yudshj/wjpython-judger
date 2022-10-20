#!/bin/bash

#./gen_tar.sh 18506

name="result"
files=""
args=("$@")
for i in $args
do
    files="$files playground/${i}_copied_code ${i}_result.csv"
    name="$name-$i"
done

echo "tar cvzf ${name}.tar.gz $files"
