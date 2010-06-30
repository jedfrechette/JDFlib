#! /bin/sh
#No comments as this is very last-minute...
#Basically, it's just a simple demonstartion that the unfolding looks like it works

R=-Rd
J=-JA0/0/6i
B=-Bg10

outfile=junk.ps

line=10/350
Hplane=190/10
Dplane=130/45

psbasemap $R $J $B -K -P > $outfile
echo $line | stereonet --lines | psxy $R $J -O -K -Sc5p -Ggreen>> $outfile
echo $Hplane | stereonet | psxy $R $J -O -K -M -W2p/blue >> $outfile
echo $Dplane | stereonet | psxy $R $J -O -K -M -W2p/green >> $outfile
echo $line H $Hplane | stereonet --lines | psxy $R $J -O -K -Sa10p -Gred >> $outfile
echo $Dplane H $Hplane | stereonet | psxy $R $J -O -M -W2p/red >> $outfile

okular $outfile
