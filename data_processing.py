#!/usr/bin/env python3

import io
import sys
import getopt
import os


# Open the file we're going to output to
# Open the directory
# Get a list of files
# for each file in the directory
# open the file and read a line
# If the line starts with "GPS:" pull it aside as a header
# insert a "millis()" at the start of the line
# Write the result to the output file
# only keep the first one like this we find
# Other than that, it needs to start with an integer.
# Because I was dumb, the first split is across a colon
# The first is milliseconds since boot.
# split everything else across commas
# Write out a join across commas to the output file

###############################
# Process the arguments and make sure they're valid
###############################
def process_args(inArgs):
    idir = None
    ofile = None
    force = False
    usage = "Usage: data_processing.py -i <input directory> -o <output directory>"
    try:
        # allow -i or --inputDir, -o or --outputFile, and -h.
        opts, args = getopt.getopt(inArgs, "hfi:o:", ["inputDir", "outputFile", "force"])
        if len(inArgs) < 4:
            raise getopt.GetoptError('Not enough arguments provided.')
    except getopt.GetoptError as err:
        print(err.msg)
        print(usage)
        sys.exit(2)

    for opt, arg in opts:
        if opt == "-h":
            print(usage)
        elif opt == "-f":
            force = True
        elif opt == "-i":
            print('Input dir: {0}'.format(arg))
            idir = arg
            if not os.path.isdir(idir):
                print("Error: Input directory {0} is not a directory.".format(arg))
                print(usage)
                sys.exit(-1)
        elif opt == "-o":
            print('Output file: {0}'.format(arg))
            if os.path.isfile(arg) and force:
                # Go ahead and use the file. We'll just overwrite it.
                print("File {0} already exists. Overwriting.".format(arg))
                ofile = arg
            elif os.path.isfile(arg) and not force:
                # Don't force it, so print error and exit.
                print("File {0} already exists. Aborting.".format(arg))
                sys.exit(-1)
            else:
                ofile = arg
        elif opt == "-":
            # We don't actually detect this, but sending a - on its own kills further
            # processing. Not sure why. Will find out later.
            print("What?")
        else:
            print("Unrecognized option: {0}".format(arg))

    if not idir or not ofile:
        # If we didn't get anything, due to strange behavior I have to look up,
        # abort and print an error.
        print("Error: Unknown problem with arguments. Unable to parse.")
        print(usage)
        sys.exit(-1)

    return idir, ofile


###############################
# Get a list of files from the input directory
# and filter the .csv files.
###############################
def print_contents(inDir):
    full_files = []
    for dPath, dName, fname in os.walk(inDir, topdown=True):
        for f in fname:
            if f[-4:] == ".csv":
                full_files.append(os.path.join(dPath, f))
    full_files.sort()
    for i in full_files:
        print(i)






###############################
# Main function
###############################
def main(argv):

    inputdir, outfile = process_args(argv)

    print_contents(inputdir)

if __name__ == "__main__":
    main(sys.argv[1:])
