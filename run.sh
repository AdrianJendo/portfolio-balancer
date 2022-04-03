#!/bin/bash
#or whatever shell you use
cd /Users/adrian/Desktop/portfolio-rebalancer
. /Users/adrian/.local/share/virtualenvs/portfolio-rebalancer-qy1tCX5O/bin/activate
# you should specifiy the python version in the below command
#python2.7 start.py >> /Users/X/Code/python/example/log.txt 2>&1
python main.py -v -s $1 -f $2 -p $3