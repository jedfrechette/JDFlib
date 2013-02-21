#!/bin/sh
#
# Normalize exr files and save the new files to an output directory.
#
# Usage: exrnormalize_batch.sh -o directory input_file [...input_files]

set -- `getopt "o:" "$@"` || {
    echo "Usage: `basename $0` -o directory input_file [...input_files]" 1>&2
    exit 1
}

outdir=NONE
while :
do
    case "$1" in
    -o) shift; outdir="$1" ;;
    --) break;;
    esac
    shift
done
shift

if [ ! -d "$outdir" ]; then
    mkdir "$outdir"
fi

for exrfile 
do
    exrnormalize "$exrfile" "$outdir/$exrfile"
done


