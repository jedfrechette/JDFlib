#! /bin/sh

#Make a contour plot of poles to planes from a file containing several measurements.

#------------------------------------------------------
#-------------Setup------------------------------------
#------------------------------------------------------

#--Bin width-------------------------------------------
#  There are algorithms for calculating the optimal bin
#  width, but I haven't bothered with them here.  It's
#  best to be aware what you're using, regardless!
filterwidth=30

#--Region, boundary, and projection--------------------
R='-Rd'
J='-JA0/0/6i'
B='-Bg10'

#--Input File-------------------------------------------
datfile='ExampleData_Planes.txt'
numdata=$(cat $datfile |wc -l)    #Number of lines in $datfile

#--Output Files-----------------------------------------
outfile='test.ps'
grid='test.grd'
cpt='test.cpt'
filtergrid='testfilter.grd'
cellsize=0.5

#-------------------------------------------------------
#-----------Plotting------------------------------------
#-------------------------------------------------------
gmt_bin='/usr/lib/gmt/bin'

$gmt_bin/psbasemap $R $J $B:."Example Contour Plot":  -Y1.5i -P -K > $outfile


#--Make the grid for contouring-------------------------
#   Output poles as x,y, then count up num of points in each cell
stereonet --poles $datfile | awk '{print $0, "1"}' | $gmt_bin/xyz2grd -G$grid -An -I$cellsize -N0 $R

#   Use a guassian filter as a kernel function to estimate density of data per unit area
$gmt_bin/grdfilter $grid -Fg$filterwidth -D0 -G$filtergrid 

#   Convert units to percent (1-100) per sq. degree
scalefac=$(echo "scale=5; 100 * $filterwidth^2 / (2*3.14 * $numdata * $cellsize^2)" | bc) 
$gmt_bin/grdmath  $filtergrid $scalefac MUL = $filtergrid
#-------------------------------------------------------



#--Plot the grid----------------------------------------
$gmt_bin/grd2cpt $filtergrid -Cjet -Z > $cpt
$gmt_bin/grdimage $filtergrid $R $J -C$cpt -O -K >> $outfile
$gmt_bin/grdcontour $filtergrid -C1 $J -O -K >> $outfile

#--Overlay each measurement-----------------------------
stereonet --poles $datfile | $gmt_bin/psxy $R $J -Ggreen -Sc5p -O -K >> $outfile

#--Scalebar---------------------------------------------
$gmt_bin/psscale -D3i/-0.2i/5i/0.2ih -B1:"Percent of dataset per sq. degree": -C$cpt -O -K >> $outfile

#--Close things up--------------------------------------
$gmt_bin/psbasemap $R $J $B -O >> $outfile

#--View output------------------------------------------
#gs $outfile
