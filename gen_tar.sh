#!/bin/bash

# This script generates a tar file of the current directory.
# Copy 选课名单.xls to the current directory.
# The header of the xls file is: 学号	姓名	性别	系所名称	专业名称	年级	教学班号	学生来源	中期退课状态
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