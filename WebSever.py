"""
================
@author: Kuangxun
@time: 2023/12/11:9:52
@IDE: PyCharm
================
"""
import socket

def handle_request(request):
    # 解析请求
    request_lines = request.split('\r\n')
    request_line = request_lines[0].split()

    # 获取请求的方法、路径和协议版本
    method = request_line[0]
    path = request_line[1]
    protocol = request_line[2]

    # 处理 GET 请求
    if method == 'GET':
        try:
            # 读取请求的文件内容
            with open('.' + path, 'rb') as file:
                content = file.read()

            # 构建 HTTP 响应
            response = "HTTP/1.1 200 OK\r\n\r\n" + content.decode('utf-8')
        except IOError:
            # 文件不存在时返回 404 错误
            response = "HTTP/1.1 404 Not Found\r\n\r\nFile Not Found"
    else:
        # 不支持的方法返回 501 错误
        response = "HTTP/1.1 501 Not Implemented\r\n\r\nMethod Not Implemented"

    return response

def start_server(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(1)

    print(f"Serving on {host}:{port}...")

    while True:
        client_socket, client_address = server_socket.accept()
        request = client_socket.recv(1024)
        # recv(1024): 这是套接字对象的 recv 方法，用于从连接中接收数据。参数 1024 指定一次最多接收的字节数。它表示从连接中尝试接收最多 1024 字节的数据.这里是字节序列
        print(request)
        request = request.decode('utf-8')
        # decode('utf-8') 的作用是将字节序列（bytes）解码为字符串
        # 字节序列（Bytes）是计算机中用于表示二进制数据的一种数据类型。在Python中，字节序列由bytes类型表示。它是不可变的序列，其中的每个元素都是0到255之间的整数，即一个字节。
        print()
        print(request)
        response = handle_request(request)
        client_socket.sendall(response.encode('utf-8'))
        client_socket.close()

if __name__ == "__main__":
    host = '127.0.0.1'
    port = 8080
    start_server(host, port)
