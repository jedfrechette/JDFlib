from os.path import split, splitext
from subprocess import call
from sys import argv

files = argv[1:]

for file in files:
    print file
#    out_name = '.'.join([splitext(split(file)[1])[0], 'csv'])
    args = ['ogr2ogr', '-overwrite', '-f', 'CSV', 'csv', file]
    print ' '.join(args)
    call(args)
