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
    timeLeft = timeout  # 用来记录在执行select函数等待ICMP回复期间剩余的时间

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

        if pID == ID:  # Confirm that this reply corresponds to the previous request
            timeSent = struct.unpack("d", recPacket[28:])[0]
            delay = (timeReceived - timeSent) * 1000

            # Handle different types of ICMP error codes
            if type == 0:  # Echo Reply
                return f"Reply from {addr[0]}: bytes=64 time={delay:.2f}ms"
            elif type == 3 and code == 0:  # Destination Network Unreachable
                return "Destination Network Unreachable"
            elif type == 3 and code == 1:  # Destination Host Unreachable
                return "Destination Host Unreachable"
            else:
                return f"ICMP Error: Type={type}, Code={code}"

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
        myChecksum = socket.htons(myChecksum) & 0xffff#Convert host byte order to network byte order
    else:
        myChecksum = socket.htons(myChecksum)



    header = struct.pack("BBHHH", ICMP_ECHO_REQUEST, 0,  myChecksum, ID, 1)
    packet = header + data

    icmpSocket.sendto(packet, (destAddr, 1))


def doOnePing(destAddr, timeout):
    icmp = socket.getprotobyname("icmp")
    icmpSocket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)

    myID = os.getpid() & 0xFFFF  # Get the pid of the current process
    sendOnePing(icmpSocket, destAddr, myID)
    delay = receiveOnePing(icmpSocket, myID, timeout, time.time())

    icmpSocket.close()
    return delay


def ping(host, count=4, timeout=1):
    dest = socket.gethostbyname(host)
    print(f"Pinging {host} [{dest}] with 64 bytes of data:")

    delays = []  # List for storing delays
    sent_packets = 0
    received_packets = 0

    i = 0
    while i < count:
        delay = doOnePing(dest, timeout)
        print(delay)

        if delay != "Request timed out.":
            delays.append(float(delay.split('=')[-1][:-2]))  # Extract delay value and add to list
            received_packets += 1
        else:
            print("Packet loss: Request timed out.")
        sent_packets += 1

        time.sleep(1)  # Requested once per second
        i += 1

    # Calculate minimum, average and maximum delays after stopping measurement
    if delays:
        min_delay = min(delays)
        max_delay = max(delays)
        avg_delay = sum(delays) / len(delays)
        print(f"Minimum Delay: {min_delay:.2f}ms")
        print(f"Average Delay: {avg_delay:.2f}ms")
        print(f"Maximum Delay: {max_delay:.2f}ms")

    # Calculate packet loss rate
    packet_loss = ((sent_packets - received_packets) / sent_packets) * 100
    print(f"Packet Loss: {packet_loss:.2f}% ({sent_packets - received_packets}/{sent_packets})")


# Taking an IP or host name as an argument
user_input = input("Please input <host or ip>: ")
count_input = input("Please input measurement count (default is 4): ")
timeout_input = input("Please input timeout in seconds (default is 1): ")

if count_input.isdigit() and timeout_input.isdigit():
    ping(user_input, count=int(count_input), timeout=int(timeout_input))
elif count_input.isdigit():
    ping(user_input, count=int(count_input))
elif timeout_input.isdigit():
    ping(user_input, timeout=int(timeout_input))
else:
    ping(user_input)



