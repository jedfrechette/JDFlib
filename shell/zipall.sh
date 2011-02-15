#!/bin/bash

# Move all files given on command line into individual zip files.

for f in "$@"
    do
    zip -r -m "$f.zip" "$f"
done
