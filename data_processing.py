#!/usr/bin/env python3

import io
import sys
import getopt


###############################
# Parse arguments that come in
###############################
def main(argv):
    usage = "Usage: data_processing.py -i <input directory> -o <output directory>"
    try:
        opts, args = getopt.getopt(argv, "hi:o:", ["inputDir=", "outputFile"])
        if len(argv) < 2:
            raise getopt.GetoptError('No arguments provided.')
    except getopt.GetoptError:
        print(usage)
        sys.exit(2)
    for opt, arg in opts:
        if opt == "-h":
            print(usage)
        elif opt == "-i":
            print('Input dir: {0}'.format(arg))
        elif opt == "-o":
            print('Output file: {0}'.format(arg))


if __name__ == "__main__":
    main(sys.argv[1:])
