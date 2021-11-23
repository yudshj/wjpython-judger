name="result"
files=""
for i in hw1 hw2 hw3
do
    files="$files playground/${i}/copied_code ${i}_result.csv"
    name="$name-$i"
done

echo "tar cvzf ${name}.tar.gz $files"
