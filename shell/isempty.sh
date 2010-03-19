#!/bin/sh

if [ "$(ls -A $1)" ]; then
  exit  
else
  exit 1
fi
