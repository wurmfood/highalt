#!/usr/bin/env python3

import os
import sys
import threading
import logging
import picamera


# Define our camera thread
class CameraThread (threading.Thread):
    def __init__(self, output_directory, video_duration, video_count):
        logging.debug('Creating new camera thread.')
        threading.Thread.__init__(self)
        self.__threadPath, self.__video_duration, self.__video_count = output_directory, video_duration, video_count
        self.__stop = False
        # self.threadPath = os.path.join(output_directory, '{:04d}'.format(instance_num))
        logging.info('Creating new directory for video: {0}'.format(self.__threadPath))
        os.mkdir(self.__threadPath)

    def stop(self):
        self.__stop = True

    def gen_paths(self, file_list):
        tmp_array = []
        for i in file_list:
            tmp_array.append(os.path.join(self.__threadPath, i))
        return list(tmp_array)

    def run(self):
        # Start a camera instance
        logging.debug('Camera thread running.')
        try:
            with picamera.PiCamera() as camera:
                logging.debug('Camera instance created. Setting options.')
                # Setup basic options
                camera.vflip = True
                camera.hflip = True
                # 480p
                # camera.resolution = (720, 480)
                # 720p
                camera.resolution = (1280, 720)
                # 1080p
                # camera.resolution = (1920, 1080)
                camera.framerate = 30
                # Record a sequence of videos
                for filename in camera.record_sequence(
                        (self.gen_paths('%08d.h264' % i for i in range(0, self.__video_count))),
                        quality=20):
                    logging.debug('Camera Thread: Recording to file: {0}'.format(filename))
                    if self.__stop:
                        break
                    else:
                        camera.wait_recording(self.__video_duration)
        except threading.ThreadError as err:
            logging.warning('Camera Thread: Caught an exception. Closing thread.')
            logging.warning('Camera Thread: Exception: {0}'.format(err.args[0]))


class CamThreadSupervisor (threading.Thread):
    def __init__(self, video_directory, video_duration, video_count):
        threading.Thread.__init__(self)
        self.video_directory = video_directory
        self.video_duration = video_duration
        self.video_count = video_count
        self.__stop = False
        self.__curThread = None
        self.__curThreadNum = 0

    def stop(self):
        self.__stop = True
        if self.__curThread:
            self.__curThread.stop()

    def run(self):
        while not self.__stop:
            # Create a new directory
            path = os.path.join(self.video_directory, '{:04d}'.format(self.__curThreadNum))
            logging.info("Cam Supervisor: Using directory: {1}".format(path))
            # Create a thread
            logging.info("Cam Supervisor: Starting new thread, number {1}".format(self.__curThreadNum))
            self.__curThread = CameraThread(path, self.video_duration, self.video_count)
            # Start the thread
            logging.info("Cam Supervisor: Starting thread.")
            self.__curThread.start()
            # Increment our thread number
            self.__curThreadNum += 1
            # Join
            logging.info("Cam Supervisor: Joining thread.")
            self.__curThread.join()
            logging.info("Cam Supervisor: Thread ended.")


if __name__ == "__main__":
    import getopt

    debugLevel = logging.DEBUG
    logging.basicConfig(stream=logging.StreamHandler(),
                        format='%(asctime)s %(levelname)s:%(message)s',
                        level=debugLevel)

    def process_args(inArgs):
        out = os.getcwd()
        dur = 5
        num = 4
        usage = """
        -o, --outDir    Where to output the videos.
        -t, --time      Duration of each video.
        -n, --num       Number of videos to save.
        """

        try:
            # allow -o or --outDir, -t or --time, -n or --num, and -h.
            opts, args = getopt.getopt(inArgs, "ho:t:n:", ["outDir", "time", "num"])

        except getopt.GetoptError as err:
            print(err.msg)
            print("\n")
            print(usage)
            sys.exit(2)

        for opt, arg in opts:
            if opt == "-h":
                print(usage)
            elif opt == "-n":
                num = arg
                print("{0} videos will be recorded.")
            elif opt == "-t":
                dur = arg
                print('Video duration: {0} sec'.format(arg))
            elif opt == "-o":
                out = arg
                print('Output Dir: {0}'.format(arg))
            elif opt == "-":
                # We don't actually detect this, but sending a - on its own kills further
                # processing. Not sure why. Will find out later.
                print("What?")
            else:
                print("Unrecognized option: {0}:{1}".format(opt, arg))

        return out, dur, num

    output, duration, count = process_args(sys.argv[1:])
    sup = CamThreadSupervisor(output, duration, count)
    sup.start()
    sup.join()
