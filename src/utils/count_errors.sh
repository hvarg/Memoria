#!/bin/bash

for r in */*.result; do
    cat $r | grep 'HTTP Error' > /dev/null && echo $r $(cat $r) >> error_list ;
done
