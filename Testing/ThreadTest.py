#!/usr/bin/env python3

import threading
from time import sleep


class TestThread (threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        sleep(5)


class TestThreadSupervisor (threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.__stop = False

    def stop(self):
        self.__stop = True

    def run(self):
        while not self.__stop:
            print("Create thread")
            new_thread = TestThread()
            print("Start new thread")
            new_thread.start()
            print("Join")
            new_thread.join()
            print("Post join")

if __name__ == "__main__":
    sup = TestThreadSupervisor()
    sup.start()
    sleep(30)
    sup.stop()
