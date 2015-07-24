#!/usr/bin/env python3

import threading
from time import sleep


class TestThread (threading.Thread):
    def __init__(self, h_array, line):
        threading.Thread.__init__(self)
        self.headers = h_array
        self.line = None

    def run(self):
        for i in range(1, 15):
            self.headers.append(i)
        self.line = "Blah"
        sleep(5)


class TestThreadSupervisor (threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.__stop = False
        self.__h_array = []
        self.__text = None
        self.__cur_thread = None

    def stop(self):
        self.__stop = True

    def print_headers(self):
        for i in self.__h_array:
            print(i)

    def print_line(self):
        print(self.__cur_thread.line)

    def run(self):
        while not self.__stop:
            print("Create thread")
            self.__cur_thread = TestThread(self.__h_array, self.__text)
            print("Start new thread")
            self.__cur_thread.start()
            print("Join")
            self.__cur_thread.join()
            print("Post join")

if __name__ == "__main__":
    sup = TestThreadSupervisor()
    sup.start()
    sleep(12)
    sup.print_line()
    sleep(4)
    sup.stop()
    sup.print_headers()
