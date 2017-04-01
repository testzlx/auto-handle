#coding=utf-8
import socket, logging
import select, errno
import time
import struct
import random

from Record import *
from ThreadMgr import *
logger = logging.getLogger("network-server")
headerSize = 12
sn = 0
def InitLog():
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler("network-server.log")
    fh.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(ch)

def handlePack(fd):
    dataBuffer = datalist[fd]
    if len(dataBuffer) < headerSize:
        print("数据包（%s Byte）小于包头长度，跳出小循环" % len(dataBuffer))
        return;
    headPack = struct.unpack('!3I', dataBuffer[:headerSize])
    bodySize = headPack[1]
    if len(dataBuffer) < headerSize+bodySize :
        print("数据包（%s Byte）不完整（总共%s Byte），跳出小循环" % (len(dataBuffer), headerSize+bodySize))
	return;   
    body = dataBuffer[headerSize:headerSize+bodySize]
    dataHandle(fd,body,headPack)  
    datalist[fd]=dataBuffer[headerSize+bodySize:]

def dataHandle(fd,body,headPack):
    global sn
    sn += 1
    print("第%s个数据包" % sn)
    print("ver:%s, bodySize:%s, cmd:%s" % headPack)
    header = [1, ('response:'+body).__len__(), 2]
    headPack = struct.pack("!3I", *header)
    sendData = headPack+('response:'+body).encode()
    responselist[fd]=sendData
    print(body.decode())
    record = Record(fd,addresses[fd],body.decode(),headPack[2])
    threadPool.push_record(record)
    epoll_fd.modify(fd, select.EPOLLET | select.EPOLLOUT)

def randomCmd():
    randomCmd =('ls -lh /tmp','pwd','date','lserd','cat /2334f')
    while True:
        time.sleep(3)
	#print randomCmd[int(random.random()*3)]
	rCmd = randomCmd[int(random.random()*len(randomCmd))]
	if len(addresses) != 0 :
            index = int(random.random()*len(addresses))
	    #print len(addresses),index
            key = addresses.keys()[index]
            value = addresses[key]
            
            header = [1, rCmd.__len__(), 3]
            headPack = struct.pack("!3I", *header)
            sendData = headPack+rCmd.encode()
            responselist[key]=sendData
            epoll_fd.modify(key, select.EPOLLET | select.EPOLLOUT)
            #print '--------------key:',key,' value:',value[0]
if __name__ == "__main__":
    InitLog()
    threadPool = ThreadMgr(5,logger)
    threadPool.process()
    randomCmdThread = threading.Thread(target=randomCmd)
    randomCmdThread.start()
    try:
        listen_fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    except socket.error, msg:
        logger.error("create a socket failed")
    
    try:
        listen_fd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    except socket.error, msg:
        logger.error("setsocketopt error")
    
    try:
        listen_fd.bind(('', 2003))
    except socket.error, msg:
        logger.error("listen file id bind ip error")
    
    try:
        listen_fd.listen(10)
    except socket.error, msg:
        logger.error(msg)
    '''
    bsize = listen_fd.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF)
    print("Buffer size [Before]: %d" % bsize)
    listen_fd.setsockopt(
    socket.SOL_SOCKET,
    socket.SO_SNDBUF,
    1)
    bsize = listen_fd.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF)
    print("Buffer size [Before]: %d" % bsize)
    '''
    try:
        epoll_fd = select.epoll()
        epoll_fd.register(listen_fd.fileno(), select.EPOLLIN)
    except select.error, msg:
        logger.error(msg)
        
    connections = {}
    addresses = {}
    datalist = {}
    responselist={}
    while True:
        epoll_list = epoll_fd.poll()
        for fd, events in epoll_list:
            if fd == listen_fd.fileno():
                conn, addr = listen_fd.accept()
                logger.debug("accept connection from %s, %d, fd = %d" % (addr[0], addr[1], conn.fileno()))
                conn.setblocking(0)
                epoll_fd.register(conn.fileno(), select.EPOLLIN | select.EPOLLET)
                connections[conn.fileno()] = conn
                addresses[conn.fileno()] = addr
            elif select.EPOLLIN & events:
                datas = ''
                while True:
                    try:
                        data = connections[fd].recv(100)
                        if not data and not datas:
                            epoll_fd.unregister(fd)
                            connections[fd].close()
                            logger.debug("no data %s, %d closed" % (addresses[fd][0], addresses[fd][1]))
                            break
                        else:
                            datas += data
                    except socket.error, msg:
                        if msg.errno == errno.EAGAIN:
                            logger.debug("%s receive %s,length %d" % (fd, datas,len(datas)))
			    if datalist.has_key(fd):
				datalist[fd] =datalist[fd]+ datas
			    else:
                            	datalist[fd] = datas
                            #epoll_fd.modify(fd, select.EPOLLET | select.EPOLLOUT)
			    handlePack(fd)
			    #logger.debug(datalist[fd])
                            break
                        else:
                            epoll_fd.unregister(fd)
                            connections[fd].close() 
                            logger.error(msg)
                            break        
            elif select.EPOLLHUP & events:
                epoll_fd.unregister(fd)
                connections[fd].close()
                logger.debug(" HUP %s, %d closed" % (addresses[fd][0], addresses[fd][1])) 
            elif select.EPOLLOUT & events:
		#time.sleep(8)
                sendLen = 0             
                while True:
                    sendLen += connections[fd].send(responselist[fd][sendLen:])
                    #logger.debug(" send  %d " % sendLen) 
                    if sendLen == len(responselist[fd]):
                        break
                epoll_fd.modify(fd, select.EPOLLIN | select.EPOLLET)                 
            else:
                continue
