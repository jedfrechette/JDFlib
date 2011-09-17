#!/bin/bash
VIDEOCODEC="Xvid"
AUDIOCODEC="MP3"
IFS="|"
#echo $@
for INFILE in $@ ; do
  BASE=$(basename $INFILE)
  OUTFILE=${BASE%.*}.avi
#  echo $OUTFILE
  avidemux2_cli --video-codec $VIDEOCODEC --audio-codec $AUDIOCODEC --force-alt-h264 --load "$INFILE" --save "$OUTFILE" --quit
done
