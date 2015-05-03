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
    cwd = os.getcwd()
    usage = "Usage: data_processing.py -i <input directory> -o <output directory>"

    try:
        # allow -i or --inputDir, -o or --outputFile, and -h.
        opts, args = getopt.getopt(inArgs, "hfi:o:", ["inputDir", "outputFile", "force"])
        if len(inArgs) < 4:
            raise getopt.GetoptError('Not enough arguments provided.')
    except getopt.GetoptError as err:
        print(err.msg)
        print("\n")
        print(usage)
        sys.exit(2)

    for opt, arg in opts:
        if opt == "-h":
            print(usage)
        elif opt == "-f":
            force = True
            print("Force true. Will overwrite out file.")
        elif opt == "-i":
            print('Input dir: {0}'.format(arg))
            idir = arg
        elif opt == "-o":
            print('Output file: {0}'.format(arg))
            ofile = arg
        elif opt == "-":
            # We don't actually detect this, but sending a - on its own kills further
            # processing. Not sure why. Will find out later.
            print("What?")
        else:
            print("Unrecognized option: {0}".format(arg))

    # Verify the arguments are good:
    # idir needs to be a directory.
    if not os.path.isdir(idir):
        print("Error: Input directory {0} is not a directory.".format(idir))
        print("\n")
        print(usage)
        sys.exit(-1)

    # Build a full path for the outfile.
    outpath = os.path.normpath(os.path.join(cwd, ofile))
    # Get just the directory part of the full path so we can test it.
    outpathdir, _ = os.path.split(outpath)

    # Check to see if the outpathdir is possibly writable.
    if os.access(outpathdir, os.W_OK) and os.access(outpathdir, os.X_OK):
        # Output file can be written to, we think.
        # If outpath already exists, check to see if force is on. If not, abort.
        if os.path.isfile(outpath) and force:
            # Go ahead and use the file. We'll just overwrite it.
            print("File {0} already exists. Overwriting.".format(outpath))
        elif os.path.isfile(outpath) and not force:
            # Don't force it, so print error and exit.
            print("File {0} already exists. Aborting.".format(outpath))
            sys.exit(-1)
        else:
            # Something else is wrong with the output
            print("Problem with the output file. Did you pass a directory? Aborting.")
            sys.exit(-1)
    else:
        print("We don't have permission to write to the target. Aborting.")
        sys.exit(-1)

    # If either idir or ofile are not set somehow, abort.
    if not idir or not ofile:
        # If we didn't get anything, due to strange behavior I have to look up,
        # abort and print an error.
        print("Error: Unknown problem with arguments. Unable to parse.")
        print("\n")
        print(usage)
        sys.exit(-1)
    else:
        return idir, outpath


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
