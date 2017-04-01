#!/usr/bin/python
#encoding=utf-8

import os
import sys
import time
import datetime
import logging
import redis

import threading
import time
import redis
#import db_conf

class GPSThread(threading.Thread):
    def __init__(self, thread_id, queue, mutex, logger):
        super(GPSThread, self).__init__()
        self.thread_id = thread_id
        self.queue = queue
        self.mutex = mutex
        self.logger = logger

    def run(self):
        #print 'thread[{0}] connect res!!!'.format(self.thread_id)
        while True:
            if len(self.queue) <= 0:
                time.sleep(0.01)
                continue
            print 'thread[{0}] get requests!!!'.format(self.thread_id)
            self.mutex.acquire()
            record = self.queue.pop(0)
            self.mutex.release()

            ret = self.process_record(record)
            if ret is False:
                print 'error process record!!! data[{0}]'.format(record.data)
                continue

    def process_record(self, record):
        return True


