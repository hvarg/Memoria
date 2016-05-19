#!/bin/bash

for r in */*.result; do
    cat $r | grep '# Empty NT' > /dev/null && echo $r >> empty_list ;
done
