#!/bin/sh

# cba to make these named arguments
# $1 = working directory
# $2 = pipenv path
# $3 = start date
# $4 = rebalance frequency
# $5 = portfolio xlsx file name (NOT path)

cd $1 # working directory
. $2 # pipenv path
python main.py -r -v -s $3 -f $4 -p $5 # start_date, frequency, portfolio