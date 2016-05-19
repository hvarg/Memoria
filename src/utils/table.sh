#!/bin/bash

echo 'directory,#query,#empty,#error' >> resume.csv
for dir in $(ls -d */); do
    n=$(ls $dir/*.sparql | wc -l)
    err=0
    emp=0
    for f in $dir/*.result; do
        cat $f | grep '# Empty NT' > /dev/null && emp=$(($emp + 1))
        cat $f | grep 'HTTP Error' > /dev/null && err=$(($err + 1))
    done
    echo $dir,$n,$emp,$err >> resume.csv
done
