#!/bin/bash

# Dir we're going to get video from
VIDEO_DIR = $1
OUT_FILE = "./output.mp4"

if [ -f $2 ]; then
    OUT_FILE = $2
fi


# First argument should be a directory. Make sure it is.
if [ -d $VIDEO_DIR ]; then
    for f in $VIDEO_DIR/*.h264;
        do echo "file '$f'" >> /tmp/video_file.list
    done

    ffmpeg -f concat -i /tmp/video_file.list -c copy /tmp/output.h264
    avconv -r 30 -i /tmp/output.h264 -vcodec copy $OUT_FILE
else
    echo "Invalid directory. Please pass a directory to the script first."
fi

