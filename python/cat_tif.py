#!/usr/bin/env python
"""Add '.tif' to the end of all files specified on the command line. If no files
are specified all files in the current directory will be used."""
import os, sys

if len(sys.argv) == 1:
    filenames = os.listdir(os.curdir)
else:
    filenames = sys.argv[1:]

for filename in filenames:
    newfilename = filename + '.tif'
    print 'Renaming', filename, 'to', newfilename, '...'
    os.rename(filename, newfilename)


