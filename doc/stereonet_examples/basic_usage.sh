#! /bin/sh

#Basic examples of plotting data on a stereonet in GMT
#This assumes you're reasonably familiar with GMT

#--Region, boundary, and projection-------------------------
R='-Rd'
J='-JA0/0/6i'
B='-Bg10'
outfile='BasicStereonet.ps'
gmt_bin='/usr/lib/gmt/bin'

#--Set up a basemap-----------------------------------------
$gmt_bin/psbasemap $R $J $B:."Example Stereonet": -P -K > $outfile

#--Plot a plane striking 320 and dipping 30 degrees to the NE 
#  (320/30NE follows the RHR, so the direction is optional)
#  Note that psxy needs the -M (multisegment) option when plotting planes
echo 320/30 | stereonet | $gmt_bin/psxy $R $J -W2p/blue -m -O -K >> $outfile

#--Plot the pole to the same plane--------------------------
#  This time we'll use an equivalent quadrant measurement
#  The input can be formatted in multiple ways, the difference
#  here is the --poles option, not the different input format.
echo S40E/30E | stereonet --poles | $gmt_bin/psxy $R $J -Sc5p -Gblue -O -K >> $outfile

#--Plot a rake along the plane------------------------------
#  This is a line (point on a stereonet) raking 45 degrees down
#  from the northwest end of the plane.  The plane is denoted
#  using yet another equivalent formatting. 
echo 140/30NE 45NW | stereonet --rakes | $gmt_bin/psxy $R $J -Sa10p -Gred -O -K >> $outfile

#--Plot the bisector of the plane and its pole--------------
#  This just to illustrate plotting the plunge/bearing of linear
#  measurements.  Note that plunge comes first! 
echo 75/050 | stereonet --lines | $gmt_bin/psxy $R $J -Sc5p -Ggreen -O >> $outfile

#gs $outfile
