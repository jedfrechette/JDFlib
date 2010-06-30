#! /bin/sh
#No comments as this is very last-minute...
#Basically, it's just a simple demonstartion that the unfolding looks like it works

R=-Rd
J=-JA0/0/6i
B=-Bg10

outfile=junk.ps
gmt_bin='/usr/lib/gmt/bin'

line=10/350
Hplane=190/10
Dplane=130/45

$gmt_bin/psbasemap $R $J $B -K -P > $outfile
echo $line | stereonet --lines | $gmt_bin/psxy $R $J -O -K -Sc5p -Ggreen>> $outfile
echo $Hplane | stereonet | $gmt_bin/psxy $R $J -O -K -m -W2p/blue >> $outfile
echo $Dplane | stereonet | $gmt_bin/psxy $R $J -O -K -m -W2p/green >> $outfile
echo $line H $Hplane | stereonet --lines | $gmt_bin/psxy $R $J -O -K -Sa10p -Gred >> $outfile
echo $Dplane H $Hplane | stereonet | $gmt_bin/psxy $R $J -O -m -W2p/red >> $outfile

#okular $outfile
