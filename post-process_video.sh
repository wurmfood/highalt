#!/bin/bash

# Dir we're going to get video from
VIDEO_DIR=$1
OUT_FILE="./output.mp4"

if [ -f $2 ]; then
    $OUT_FILE = $2
fi


# First argument should be a directory. Make sure it is.
if [ -d $VIDEO_DIR ]; then
    cd $VIDEO_DIR
    for f in ./*.h264; do
        echo "file '$f'" >> video_file.list
        echo $f
    done

    ffmpeg -f concat -i video_file.list -c copy output.h264
    avconv -r 30 -i output.h264 -vcodec copy $OUT_FILE
    rm outfile.h264
    rm video_file.list
else
    echo "Invalid directory. Please pass a directory to the script first."
fi

