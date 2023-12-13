import os
import socket

global listen_port


def handle_req(client_socket):
    # proxy使用了client_socket去和客户端通信，proxy_server_socket去监听客户端的请求，使用proxy_client_socket去与服务器沟通
    recv_data = client_socket.recv(1024).decode("UTF-8")
    request_lines = recv_data.split('\r\n')
    print()
    print(recv_data)
    request_line = request_lines[0].split()
    path = request_line[1]
    path = path.split("/")[-1]
    try:
        with open('./' + path, 'rb') as file:
            content = file.read()
        print("File is found in proxy server.")
        response = "HTTP/1.1 200 OK\r\n\r\n" + content.decode('utf-8')
        response = response.encode('utf-8')
        client_socket.sendall(response)
        client_socket.close()
        print("Send, done.")
    except FileNotFoundError as e:
        print(f"File not found: {e}\nSend request to server...")
        try:
            proxy_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_name = request_lines[1].split(":")[1]
            server_name = server_name.lstrip()
            proxy_client_socket.connect((server_name, listen_port))
            request_line = request_lines[0].split(' ')
            path = request_line[1]
            parts = path.split("/")
            path = parts[-1]

            print("-1")
            standard_request = f"GET /{path} HTTP/1.1\r\n"
            print("0")
            proxy_client_socket.sendall(standard_request.encode("UTF-8"))
            print("1")
            response_msg = proxy_client_socket.recv(4069)
            print("File is found in server.")
            client_socket.sendall(response_msg)
            print("Send, done.")
            print()
            body_start = response_msg.find(b'\r\n\r\n') + 4

            # 提取响应体
            html_content = response_msg[body_start:]

            # 将 HTML 内容保存到文件
            with open(path, 'wb') as file:
                file.write(html_content)
        except IOError:
            response = "HTTP/1.1 404 Not Found\r\n\r\n404 Not Found"
            response = response.encode('utf-8')
            client_socket.sendall(response)
            print("404 not found")
            # raise

        # raise


def start_proxy(port1):
    proxy_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy_server_socket.bind(("", port1))
    proxy_server_socket.listen(1)
    while True:
        try:
            print("Proxy is waiting for connecting...")
            client_socket, _ = proxy_server_socket.accept()
            print("Connect established")
            handle_req(client_socket)
            client_socket.close()
        except Exception as e:
            print("error: {0}".format(e))
            break
    proxy_server_socket.close()


if __name__ == '__main__':
    while True:
        port = None
        try:
            port = int(input("choose a port number over 1024:"))
            listen_port = int(input("choose a listen_port :"))
        except ValueError:
            print("Please input an integer rather than {0}".format(type(port)))
            continue
        else:
            if port <= 1024:
                print("Please input an integer greater than 1024")
                continue
            else:
                break
    start_proxy(port)
