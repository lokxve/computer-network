import os
import struct
import time
import select
import socket
from _socket import IPPROTO_IP, IP_TTL
from socket import timeout

sequence_number=1  # 设置一个初始序列号
ICMP_ECHO_REQUEST = 8  # ICMP type code for echo request messages
ICMP_ECHO_REPLY = 0  # ICMP type code for echo reply messages
ICMP_Type_Unreachable = 3  # unacceptable host
ICMP_Type_Overtime = 11  # request overtime
MAX_HOPS = 30
TIMEOUT = 3  # 设置了每个跳数的超时时间
big_end_sequence = '!bbHhh'
TRIES =3  # 每一跳的尝试次数


def checksum(strings):
    csum = 0
    count_to = (len(strings) // 2) * 2
    counts = 0
    while counts < count_to:
        this_val = strings[counts + 1] * 256 + strings[counts]
        csum = csum + this_val
        csum = csum & 0xffffffff
        counts = counts + 2
    if count_to < len(strings):
        csum = csum + strings[len(strings) - 1]
        csum = csum & 0xffffffff
    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer


def build_packet():
    global sequence_number
    identifier = os.getpid() & 0xFFFF  # Get the pid of the current process as the identifier
    icmp_checksum = 0
    # 1. Build ICMP header
    icmp_header = struct.pack(big_end_sequence, ICMP_ECHO_REQUEST, 0, icmp_checksum, identifier, sequence_number)

    time_send = struct.pack('!d', time.time())

    # 2. Checksum ICMP packet using given function
    icmp_checksum = checksum(icmp_header + time_send)
    # 3. Insert checksum into packet
    icmp_header = struct.pack(big_end_sequence, ICMP_ECHO_REQUEST, 0, icmp_checksum, identifier, sequence_number)
    # 4. Send packet using socket
    icmp_packet = icmp_header + time_send
    sequence_number += 1
    return icmp_packet


def get_route(hostname):
    print(f"通过最多 {MAX_HOPS} 个跃点跟踪")
    ip_address = socket.gethostbyname(hostname)
    print(f"到 {hostname} [{ip_address}] 的路由:\n")
    time_left = TIMEOUT

    results = []  # 存储结果

    for ttl in range(1, MAX_HOPS):
        for tries in range(TRIES):
            destination_ip = socket.gethostbyname(hostname)
            icmp_name = socket.getprotobyname('icmp')
            icmp_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp_name)
            icmp_socket.settimeout(TIMEOUT)
            icmp_socket.bind(("", 0))
            icmp_socket.setsockopt(IPPROTO_IP, IP_TTL, struct.pack('I', ttl))
            try:
                icmp_socket.sendto(build_packet(), (destination_ip, 0))
                t = time.time()
                time_begin_receive = time.time()
                if_got = select.select([icmp_socket], [], [], TIMEOUT)  # 检测是否收到报文
                time_during_receive = time.time() - time_begin_receive
                if not if_got[0]:
                    print("  %d     *        Request timed out." % ttl)

                rec_packet, addr = (icmp_socket.recvfrom(1024))
                time_received = time.time()
                time_left = time_left - time_during_receive
                if time_left <= 0:
                    print("  %d     *        Request timed out." % ttl)
            except timeout:
                continue
            else:
                byte_in_double = struct.calcsize("!d")  # 确定double在网络字节序下所占的字节数
                time_sent = struct.unpack("!d", rec_packet[28: 28 + byte_in_double])[0]
                rec_header = rec_packet[20:28]
                types, _, _, _, _ = struct.unpack(big_end_sequence, rec_header)
                result = (ttl, time_received - t * 1000, addr[0])  # 元组第一个元素是ip地址，第二个是端口
                results.append(result)

                if types == 11:
                    print("  %d    rtt=%.0f ms    %s" % (ttl, (time_received - t) * 1000, addr[0]))
                elif types == 3:
                    print("  %d    rtt=%.0f ms    %s" % (ttl, (time_received - t) * 1000, addr[0]))
                elif types == 0:
                    print("  %d    rtt=%.0f ms    %s" % (ttl, (time_received - time_sent) * 1000, addr[0]))
                    return results
                else:
                    print("error")
                continue
            finally:
                icmp_socket.close()
# 检查输入是否有效
def validate_input(input_str):
    try:
        socket.getaddrinfo(input_str, None)
        return True
    except socket.gaierror:
        return False

if __name__ == '__main__':
    while True:
        user_input = input(f"Please input <host or ip>")
        if validate_input(user_input):
            break
        else:
            print(f"Invalid input. Please enter a valid host name or IP address")
    get_route(user_input)
