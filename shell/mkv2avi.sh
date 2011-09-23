#!/bin/bash
VIDEOCODEC="Xvid"
AUDIOCODEC="MP3"
IFS="|"
for INFILE in $@ ; do
  BASE=$(basename $INFILE)
  OUTFILE=${BASE%.*}.avi
  # This will still prompt the user for each file.
  # Answer No, don't use alternate h264 read mode.
  # Answer Yes, rebuild index.
  avidemux2_cli --video-codec $VIDEOCODEC --audio-codec $AUDIOCODEC --autoindex --rebuild-index --force-b-frame --load "$INFILE" --save "$OUTFILE" --quit
done
