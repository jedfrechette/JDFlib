#!/bin/sh

# $1 End count
# $2 Resolution [Default: 150]

scanadf -d hpaio:/usb/Officejet_5600_series?serial=CN58MCF3SZ04CY --resolution ${2:-150} --mode Gray -x 215 -y 279  -e $1
unpaper image-%04d un%04d.pgm
#unpaper -l double --pre-rotate 90 n%02d.pgm un%02d.pgm
#for i in `ls un*pgm`; do pgmtopbm $i > $i.pbm; done
for i in `ls *.pgm`; do pnmtotiff $i > $i.tiff; done
tiffcp *.tiff all.tiff
tiff2pdf -z -x $1 -y $1 -o scan.pdf all.tiff

# Cleanup
/bin/rm image-*
/bin/rm un*.pgm
#/bin/rm un*.pgm.pbm
/bin/rm un*pgm.tiff
/bin/rm all.tiff
