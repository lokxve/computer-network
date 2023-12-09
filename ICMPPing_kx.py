"""
================
@author: Kuangxun
@time: 2023/11/29:4:17
@IDE: PyCharm
================
"""
#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import socket
import os
import struct
import time
import select
import sys


ICMP_ECHO_REQUEST = 8  # ICMP type code for echo request messages


def checksum(packet):
    # Calculate ICMP packet checksum
    countTo = (len(packet) // 2) * 2
    count = 0
    csum = 0

    while count < countTo:
        thisVal = packet[count + 1] * 256 + packet[count]
        csum = csum + thisVal
        csum = csum & 0xffffffff
        count = count + 2

    if countTo < len(packet):
        csum = csum + packet[len(packet) - 1]
        csum = csum & 0xffffffff

    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)

    return answer


def receiveOnePing(icmpSocket, ID, timeout, timeSent):
    timeLeft = timeout #用来记录在执行select函数等待ICMP回复期间剩余的时间

    while True:
        startedSelect = time.time()
        whatReady = select.select([icmpSocket], [], [], timeLeft)
        howLongInSelect = (time.time() - startedSelect)

        if whatReady[0] == []:  # Timeout
            return "Request timed out."

        timeReceived = time.time()
        recPacket, addr = icmpSocket.recvfrom(1024)

        icmpHeader = recPacket[20:28]
        type, code, checksum, pID, sequence = struct.unpack(
            "BBHHH", icmpHeader
        )

        if pID == ID:#确认这个回复是对应之前的请求。
            timeSent = struct.unpack("d", recPacket[28:])[0]
            delay = (timeReceived - timeSent) * 1000
            return f"Reply from {addr[0]}: bytes=64 time={delay:.2f}ms"

        timeLeft = timeLeft - howLongInSelect

        if timeLeft <= 0:
            return "Request timed out."


def sendOnePing(icmpSocket, destAddr, ID):
    # Header is type (8), code (8), checksum (16), id (16), sequence (16)
    myChecksum = 0
    # Make a dummy header with a 0 checksum
    header = struct.pack("BBHHH", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    data = struct.pack("d", time.time())

    # Calculate the checksum on the data and the dummy header.
    myChecksum = checksum(header + data)

    # Get the right checksum, and put in the header
    if sys.platform == 'darwin':
        myChecksum = socket.htons(myChecksum) & 0xffff#把主机字节序转换为网络字节序
    else:
        myChecksum = socket.htons(myChecksum)



    header = struct.pack("BBHHH", ICMP_ECHO_REQUEST, 0,  myChecksum, ID, 1)
    packet = header + data

    icmpSocket.sendto(packet, (destAddr, 1))


def doOnePing(destAddr, timeout):
    icmp = socket.getprotobyname("icmp")
    # SOCK_RAW is a powerful socket type. For more details:   http://sock-raw.org/papers/sock_raw
    icmpSocket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)

    myID = os.getpid() & 0xFFFF  # 获取当前进程的pid
    sendOnePing(icmpSocket, destAddr, myID)
    delay = receiveOnePing(icmpSocket, myID, timeout, time.time())

    icmpSocket.close()
    return delay

def ping(host, timeout=1,count=4):
    dest = socket.gethostbyname(host)
    print(f"Pinging {host} [{dest}] with 64 bytes of data:")

    i=0
    while i<count :
        delay = doOnePing(dest, timeout)
        print(delay)
        time.sleep(1)  #每秒请求一次
        i+=1
# Taking an IP or host name as an argument
user_input=input("Please input <host or ip>: ")


ping(user_input)
