#! /bin/sh

#Example of how to fit a plane to stereonet data using GMT's fitcircle

#--Setup-------------------------------
R=-Rd
J=-JA0/0/6i
B=-Bg10:.North:

outfile=FitPlane.ps
datfile=ExampleData_FitPlane.txt

psbasemap $R $J $B -K -P -Y1i > $outfile

#--Plot Data---------------------------
stereonet $datfile --lines | psxy $R $J -Sc5p -Gblue -O -K >> $outfile

#--Fit a Plane to the data-------------
#  With fitcircle, -L2 is usually better than -L1 for this purpose. 
plane=$(stereonet $datfile --lines | fitcircle -L2 | awk 'NR==2{print $1, $2}' | stereonet -I plane)

#--Plot the plane----------------------
echo $plane | stereonet | psxy $R $J -M -W2p/red -O -K >> $outfile

#--Annotate the S/D of the plane-------
pstext -R0/8/0/9 -JX8i -O  -Y-1i  <<EOF >> $outfile
3 0.7 18 0 1 cm Best Fit Plane: $(echo $plane | stereonet -C)
EOF
#stereonet -C call is for nicer formatting of the S/D of the plane

gs $outfile
