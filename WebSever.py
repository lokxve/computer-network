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

    # 处理 GET 请求
    if method == 'GET':
        try:
            # 读取请求的文件内容
            # '.' + path 的作用是将当前工作目录和请求路径结合起来，以获取请求的文件相对于服务器的路径
            with open('.' + path, 'rb') as file:  # 二进制模式读取文件，图文视频都可以  . path
                content = file.read()

            # 构建 HTTP 响应
            file_extension = path.split('.')[-1].lower()  # 获取文件拓展名

            if file_extension in ['jpg', 'jpeg', 'png', 'gif']:
                # 对于图片等二进制文件，直接发送字节串
                response = b"HTTP/1.1 200 OK\r\n\r\n" + content
            else:
                # 对于其他类型的文件（假设是文本文件），使用utf-8解码
                response = "HTTP/1.1 200 OK\r\n\r\n" + content.decode('utf-8')
                response = response.encode('utf-8')
        except IOError:
            # 文件不存在时返回 404 错误
            response = "HTTP/1.1 404 Not Found\r\n\r\nFile Not Found"
            response = response.encode('utf-8')
    else:
        # 不支持的方法返回 501 错误
        response = "HTTP/1.1 501 Not Implemented\r\n\r\nMethod Not Implemented"
        response = response.encode('utf-8')

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
        # print(request)
        request = request.decode('utf-8')
        # decode('utf-8') 的作用是将字节序列（bytes）解码为字符串
        # 字节序列（Bytes）是计算机中用于表示二进制数据的一种数据类型。在Python中，字节序列由bytes类型表示。它是不可变的序列，其中的每个元素都是0到255之间的整数，即一个字节。
        # print("\n"+request)
        response = handle_request(request)
        client_socket.sendall(response)
        client_socket.close()

if __name__ == "__main__":
    host = input("Input the host you want: ")
    port = int(input("Input the port you want: "))
    start_server(host, port)
