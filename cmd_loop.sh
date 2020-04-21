#!/bin/sh

# $1 Command
# $2 Input files

#echo $2
for i in $2; do $1 $i; done
