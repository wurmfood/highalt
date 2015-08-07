#!/usr/bin/env python3

import sys
import getopt
import os

############################
# data_processing.py
#
# Takes up to three arguments:
# -i <indir> : directory to parse for input files
# -o <outfile> : file to write the output to
# -f : force overwriting of output file if it already exists
#
# Reads in all the .csv files in a directory. It looks for a header
# that appears at the top of the files from output of the highalt Arduino code.
# The multiple files are then concatenated with a single header line.
#
############################


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
        elif os.path.exists(outpath):
            # Something else is wrong with the output
            print(outpath)
            print(outpathdir)
            print("Problem with the output file. Did you pass a directory? Aborting.")
            sys.exit(-1)
        else:
            # Everything seems to be ok.
            pass
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
def get_contents(inDir):
    full_files = []
    for dPath, dName, fname in os.walk(inDir, topdown=True):
        for f in fname:
            if f[-4:] == ".csv":
                full_files.append(os.path.join(dPath, f))
    full_files.sort()

    return full_files


###############################
# Process the file that is brought in.
# If we haven't seen a header, pull it out and start a new file with it.
# If we have, write out the line we read in, correctly formatted.
###############################
def process_file(inpath, fileout, headers_proccessed):
    with open(inpath) as filein:
        for line in filein:
            # If we haven't yet processed headers, try to find some.
            if not headers_proccessed:
                # If we have a header, all of the line should be that header.
                # To make sure, check the first nine characters of data[0].
                # (there's also a line that's GPS: OK if the gps is working right)
                if line[0:9] == "Arduino: ":
                    fileout.write(line)
                    fileout.write('\n')
                    headers_proccessed = True
                else:
                    # If it isn't, it must be something else that we're not worried about,
                    # so ignore it.
                    pass
            # So long as it's not another header line, dump it to the outfile.
            elif line[0:9] != "Arduino: ":
                fileout.write(line + '\n')
                # fileout.write('\n')
    return headers_proccessed


###############################
# Main function
###############################
def main(argv):
    # Get the input directory and output file from the arguments
    inputdir, outfile = process_args(argv)

    # Get a list of the files we're going to process
    file_list = get_contents(inputdir)

    # Have we already processed the headers?
    processed_headers = False

    # For each file we're supposed to process, send it to be processed
    # and tell the function if we've already processed the headers or not.
    try:
        # Open the file with mode 'wt'. 'w' says to overwrite the file.
        # 't' is for text mode.
        with open(outfile, mode='wt') as outfile_fd:
            for f in file_list:
                print("Reading: {0}.".format(f))
                processed_headers = process_file(f, outfile_fd, processed_headers)
    finally:
        pass


############################
# Start it all up.
############################
if __name__ == "__main__":
    main(sys.argv[1:])
