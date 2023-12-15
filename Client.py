"""
================
@author: Kuangxun
@time: 2023/12/15:15:22
@IDE: PyCharm
================
"""
import socket

def main():
    # 服务器的IP地址和端口号
    server_ip = '127.0.0.1'
    server_port = 8080

    # 创建 socket 对象
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # 连接到服务器
        client_socket.connect((server_ip, server_port))
        print('成功连接到服务器')

        while True:
            # 从用户获取输入并发送到服务器
            message = input(f'请输入要发送的消息（输入"exit"退出）: ')
            client_socket.sendall(message.encode("UTF-8"))

            # 退出循环，关闭客户端套接字
            if message.lower() == 'exit':
                break

            # 接收来自服务器的响应
            server_response = client_socket.recv(1024)
            print('来自服务器的响应:', server_response.decode())

    except ConnectionRefusedError:
        print('连接被拒绝，请确保服务器正在运行并且使用了正确的IP地址和端口号。')
    finally:
        # 关闭客户端套接字
        client_socket.close()

if __name__ == "__main__":
    main()
