import socket
import select
import sys

class clientUDP:
    def __init__(self,host="127.0.0.1",port=6666):
        self.port = port
        self.host = host
        self.client_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.timeout = 30
        self.client_socket.settimeout(self.timeout)
        self.is_running = True

    def start(self):
        while self.is_running:
            print("输入需要传输的信息：")
            try:
                ready, _, _ = select.select([sys.stdin], [], [], self.timeout)
                if ready:
                    message = input()
                    self.sendMessage(message)
                else:
                    print("client time out !")
                    self.is_running = False
                    break
            except Exception as e:
                print(f"oops! something goes wrong when sending message: {e}")




    def sendMessage(self,message):
        try:
            self.client_socket.sendto(message.encode(),(self.host,self.port))
            data,server_address = self.client_socket.recvfrom(1024)
            self.handle_response_from_server(data,server_address)
        except Exception as e:
            print(f"oops! something goes wrong when sending message: {e}")
            self.is_running = False
            self.close()


    def handle_response_from_server(self,data,server_address):
        print(f"收到{server_address} 处返回数据： {data.decode()}")

    def close(self):
        if self.client_socket:
            self.is_running = False
            self.client_socket.close()
