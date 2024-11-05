import socket
import threading
from concurrent.futures import ThreadPoolExecutor,as_completed

class serverTCP:
    def __init__(self,host='127.0.0.1',port=6666):
        '''
        指定服务器要监听的端口和host，维护一个连接到本服务器上的client列表方便后续操作
        :param host:
        :param port:
        '''
        self.port = port
        self.host = host
        self.server_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.client = []
        # 维护一个与本服务器连接的客户端列表

    def start(self,listenNum=5):
        '''
        绑定host和port，启动监听
        :param listenNum:最大监听数
        :return:
        '''
        # 思考怎么使用try-catch进行异常处理
        self.server_socket.bind((self.host,self.port))
        self.server_socket.listen(listenNum)
        print("TCP Server正在监听: Host: {} Port: {}".format(self.host,self.port))
        # while True:
        #     with ThreadPoolExecutor(max_workers=listenNum) as executor:
        #         client_socket, client_address = self.server_socket.accept()
        #         print("来自IP: {} Port: {} 的新连接已经建立".format(client_address[0], client_address[1]))
        #         tasks = [executor.submit(self.handle_client, client_socket, client_address)]
        #         for task in as_completed(tasks):
        #             task.result()
        self.accept_client()



    def accept_client(self):
        '''
        与新客户端建立连接
        :return:
        '''
        while True:
            client_socket, client_address = self.server_socket.accept()
            self.client.append(client_socket)
            print("------------------来自IP: {} Port: {} 的新连接已经建立------------------".format(client_address[0],
                                                                                                    client_address[1]))
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket, client_address))
            client_thread.start()


    def handle_client(self,client_socket,client_address):
        '''
        从客户端接收信息
        :param client_socket:
        :param client_address:
        :return:
        '''
        while True:
            try:
                message = client_socket.recv(1024)
                if message==b"":
                    break
                # 断开连接的时候message为""
                print(f"从IP：{client_address[0]} Port: {client_address[1]} 处接受到的信息: ",end='')
                self.handle_request(message)
                client_socket.send("ACK".encode("utf-8"))
            except ConnectionResetError:
                print("oops!! something goes wrong!")
                break

        client_socket.close()
        self.client.remove(client_socket)
        # 断开连接时从列表中移除对应的socket
        print(f"------------------从IP：{client_address[0]} Port: {client_address[1]} 处断开连接------------------")

    def broadcastShutdown(self):
        '''
        服务器关闭，通知所有客户端并断开连接
        :return:
        '''
        for client in self.client:
            # client.send(b'server is shutting down')
            client.close()


    def handle_request(self,message):
        '''
        处理从客户端发来的信息
        :param message:
        :return:
        '''
        print(message.decode("utf-8"))

