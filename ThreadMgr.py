#!/usr/bin/python
#encoding=utf-8

import os
import sys
import time
import datetime
import logging
import redis

from Thread import GPSThread
import threading

class ThreadMgr:
    def __init__(self, thread_num=1, logger=None):
        self.thread_num = thread_num
        self.threads = []
        self.queues = []
        self.mutexs = []
        self.logger = logger
        for i in range(self.thread_num):
            self.queues.append( [] )
            self.mutexs.append( threading.Lock() )
            self.threads.append( GPSThread(i, self.queues[i], self.mutexs[i], logger) )

    def push_record(self, record):
        thread_id = self.hash_id(record.host_fd) % self.thread_num
        self.mutexs[thread_id].acquire()
        self.queues[thread_id].append(record)
        self.mutexs[thread_id].release()
        print 'thread[{0}] process the record[{1}]'.format(thread_id, record.data)
        return True

    def process(self):
        for i in range(self.thread_num):
            self.threads[i].start()

    def end_process(self):
        for i in range(self.thread_num):
            if self.threads[i] is threading.currentThread():
                continue
            self.threads[i].join()

    def hash_id(self, g_id):
        return int(g_id)
