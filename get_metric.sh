#!/bin/bash

result=`cat $1 | awk '/- - - - - - - - - - - - - - - - - - - - - - - - -/{flag=1;next}/iperf Done./{flag=0}flag' | tail -n +2 | head -n 1 | awk '{print $8}'`
echo $result
