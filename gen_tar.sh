#!/bin/bash
# This script generates a tar file of the current directory.
# Place code directory which was extracted from the tar ball in `./playground`\
# and run this script from the root directory of the project.
# Command: `./gen_tar.sh hw1 hw2 12345 <code_dir_name> ...`
name="result"
files=""
args="$@"
for i in $args
do
    python3 ./judger.py $i
    files="$files playground/${i}_copied_code ${i}_result.csv"
    name="$name-$i"
done
name="${name}.tar.gz"
tar czf $name $files
echo "Generated $name"