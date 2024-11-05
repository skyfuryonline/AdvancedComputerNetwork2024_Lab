import socket
import threading

class serverUDP:
    def __init__(self,host="127.0.0.1",port=8888):
        '''
        UDP 本身不需要建立连接，它可以处理来自不同客户端的数据包。
        实现多客户端支持的关键是在服务器端能够同时接收和回复来自多个客户端的请求，
        而不需要像 TCP 那样维护每个客户端的连接。

        因为无连接的方式，当服务器关闭时不需要切断和客户端的连接？发送一条数据通知所有连接过的客户端？
        :param host:
        :param port:
        '''
        self.host = host
        self.port = port
        self.server_socket= socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

    def start(self):
        self.server_socket.bind((self.host,self.port))
        print("UDP Server正在监听: Host: {} Port: {}".format(self.host, self.port))
        self.listen()


    def listen(self):
        while True:
            data,client_address = self.server_socket.recvfrom(1024)
            print(f"------------------来自IP: {client_address[0]} Port: {client_address[1]}------------------")
            response = self.handle_request(data.decode())
            try:
                self.server_socket.sendto(response.encode(),client_address)
            except Exception as e:
                print(f"oops! something goes wrong when sending message to {client_address} :{e}")

    def handle_request(self,data):
        print(f"数据： {data}")
        return "check"

    def shutdown(self):
        if self.server_socket:
            self.server_socket.close()
        print("server is shutting down !")
