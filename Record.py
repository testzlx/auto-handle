#!/usr/bin/python
#encoding=utf-8

class Record:
    def __init__(self,fd,remote_ip,data,cmd_type):
        self.host_fd = fd
	self.data = data
	self.remote_ip = remote_ip
	self.cmd_type = cmd_type
