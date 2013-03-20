#!/bin/bash -x

## Test to see if the system has the proper applications installed
if [ ! -f dcraw ] && [ dcraw == "0" ];
then
    echo "You do not have the dcRAW application installed."
    echo "This script will not run without it."
    echo "Please install the application."
    exit 0
fi

dcraw2ln ()
{
    # These calls could be piped together to prevent creating the extra .tiff
    dcraw -v -j -w -W -6 -T -H 0 -o 0 -q 3 -g 1 1 ${1};
    file_extention=$(echo ${1} | sed 's/^.*\(\.[^.]*\)$/\1/')
	file_name=$(echo ${1} | sed "s/$file_extention//")
	convert $file_name.tiff -compress Zip $file_name\_ln16.tif
    exiftool -overwrite_original -TagsFromFile ${1} $file_name\_ln16.tif
    convert $file_name\_ln16.tif -compress Zip $file_name\_lnh.exr
    # /bin/rm $file_name.tiff
}

dcraw2srgb8 ()
{
    dcraw -v -j -w -W -T -H 0 -o 1 -q 3 -g 2.4 12.92 ${1};
    file_extention=$(echo ${1} | sed 's/^.*\(\.[^.]*\)$/\1/')
	file_name=$(echo ${1} | sed "s/$file_extention//")
	convert $file_name.tiff -compress Zip $file_name\_srgb8.tif
    exiftool -overwrite_original -TagsFromFile ${1} $file_name\_srgb8.tif
    #/bin/rm $file_name.tiff
}


process ()
{
    if [ -d "$1" ];
    then

	dir="$1"

 ## Convert every CR2 file in the directory to tif
	if [ "$(ls $dir/*.CR2)" != "" ]; 
	then
	    echo "Converting CR2 files to tif"
	    for i in $(ls $dir/*.CR2); do
		dcraw2srgb8 $i
        dcraw2ln $i
	    done
	else
	    echo "No CR2 Files, Moving On"
	fi

	if [ "$(ls $dir/*.NEF)" != "" ];
	then
	    echo "Converting NEF files to tif"
	    for j in $(ls $dir/*.NEF); do
		dcraw2srgb8 $j
        dcraw2ln $j
	    done
	else 
	    echo "No NEF Files, Moving On"
	fi

    fi

    if [ -f "$1" ]; 
    then
	frame="$1"
	dir=$(dirname $frame)
	file_extention=$(echo $frame | sed 's/^.*\(\.[^.]*\)$/\1/')
	file_name=$(echo $frame | sed "s/$file_extention//")
	if [ "$file_extention" == ".CR2" ];
	then
	    echo "Converting CR2 file to tif"
	    dcraw2srgb8 $frame
        dcraw2ln $frame
	fi
	if [ "$file_extention" == ".NEF" ];
	then
	    echo "Converting NEF file to tif"
	    dcraw2srgb8 $frame
        dcraw2ln $frame
	fi

    fi
}

 ## End Functions
 ##################################################
 ## Argument Conditions

if [ "$1" = "" ];
then
    dir="."
 ## Run the script in the current directory and process everything
    process $dir

elif [ -d "$1" ];
then
    process "$1"

elif [ -f "$1" ];
then
    frame="$1"

## User may have submitted the file with the full path included
    if [ -d $(dirname $frame) ] && [ $(dirname $frame) != "." ];
    then
	echo "It appears that you gave us the full file path"
	dir=$frame

	process $dir

    elif [ $(pwd) != "/" ];
    then
	if [ -f $(pwd)/$frame ];
	then

	    dir=$(pwd)/$frame

	    process $dir
	fi ## End of the if [ -f $(pwd)/$frame ]; statement

    else
	echo "You are not in the Proper directory to be submitting the file name,"
	echo "or your path is invalid. Please look at the info you are passing the script"


    fi



else
    clear
    echo ""
    echo "You are not using the script correctly"
    echo ""
    echo "Please enter the 'raw2tif' command followed by a space and then one of three things"
    echo ""
    echo "1)The full path to the folder containing the files you wish to have processed"
    echo "2)The full path to a file in the folder containing the files you with to processed"
    echo "3)If you are in the folder you wish to render, just a file name from the sequence"
    echo ""
    echo "If you have any questions or issues, please ask."
    echo "Thank you"
fi
