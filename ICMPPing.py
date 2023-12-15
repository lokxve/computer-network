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
    count_to = (len(packet) // 2) * 2
    count = 0
    csum = 0

    while count < count_to:
        this_val = packet[count + 1] * 256 + packet[count]
        csum = csum + this_val
        csum = csum & 0xffffffff
        count = count + 2

    if count_to < len(packet):
        csum = csum + packet[len(packet) - 1]
        csum = csum & 0xffffffff

    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)

    return answer


def receiveOnePing(icmp_socket, ID, timeout):
    time_left = timeout  # 用来记录在执行select函数等待ICMP回复期间剩余的时间

    while True:
        started_select = time.time()
        what_ready = select.select([icmp_socket], [], [], time_left)
        how_long_in_select = (time.time() - started_select)

        if not what_ready[0]:  # Timeout
            return "Request timed out."

        time_received = time.time()
        rec_packet, addr = icmp_socket.recvfrom(1024)

        icmp_header = rec_packet[20:28]
        type, code, my_checksum, p_id, sequence = struct.unpack("!BBHHH", icmp_header)

        if p_id == ID:  # Confirm that this reply corresponds to the previous request
            time_sent = struct.unpack("d", rec_packet[28:])[0]
            delay = (time_received - time_sent) * 1000

            # Handle different types of ICMP error codes
            if type == 0:  # Echo Reply
                return f"Reply from {addr[0]}: bytes=64 time={delay:.2f}ms"
            elif type == 3 and code == 0:  # Destination Network Unreachable
                return "Destination Network Unreachable"
            elif type == 3 and code == 1:  # Destination Host Unreachable
                return "Destination Host Unreachable"
            else:
                return f"ICMP Error: Type={type}, Code={code}"

        time_left = time_left - how_long_in_select

        if time_left <= 0:
            return "Request timed out."



def sendOnePing(icmp_socket, des_addr, ID):
    # Header is type (8), code (8), checksum (16), id (16), sequence (16)
    my_checksum = 0
    # Make a dummy header with a 0 checksum
    header = struct.pack("!BBHHH", ICMP_ECHO_REQUEST, 0, my_checksum, ID, 1)
    data = struct.pack("d", time.time())

    # Calculate the checksum on the data and the dummy header.
    my_checksum = checksum(header + data)

    header = struct.pack("!BBHHH", ICMP_ECHO_REQUEST, 0, my_checksum, ID, 1)
    packet = header + data

    icmp_socket.sendto(packet, (des_addr, 1))


def doOnePing(des_addr, timeout):
    icmp = socket.getprotobyname("icmp")
    icmp_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)

    my_id = os.getpid() & 0xFFFF  # Get the pid of the current process
    sendOnePing(icmp_socket, des_addr, my_id)
    delay = receiveOnePing(icmp_socket, my_id, timeout)

    icmp_socket.close()
    return delay


def ping(host, count=4, timeout=1):
    des = socket.gethostbyname(host)
    print(f"Pinging {host} [{des}] with 64 bytes of data:")

    delays = []  # List for storing delays
    sent_packets = 0
    received_packets = 0

    i = 0
    while i < count:
        delay = doOnePing(des, timeout)
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



