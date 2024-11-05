import select
import socket
import sys
import threading
import time


class clientTCP:
    def __init__(self,host="127.0.0.1",port=6666):
        '''
        1.设定客户端的相应socket信息，设置超时参数，设置标记位判断连接情况
        2.客户端自己的端口：通常是由操作系统自动分配的，不需要手动指定。
        服务器通常监听一个固定的端口，而客户端则使用一个随机的临时端口进行通信。
        :param host:服务器ip
        :param port: 服务器port
        '''
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.timeout = 30
        self.client_socket.settimeout(self.timeout)
        # 设置超时时间
        # 注意使用的方法，是抛出异常
        self.is_running = True
        # 该标记位记录是否与服务器保持连接，listen_for_server中如果连接中断，将被设置为false

    def connect(self):
        # 客户端连接服务器
        self.client_socket.connect((self.host,self.port))
        print(f"与IP: {self.host} PORT: {self.port} 成功建立连接！")

    def listen_for_server(self):
        '''
        用新线程执行该函数，监听服务器状态，如果服务器断开/超时则切断与服务器的连接
        :return:
        '''
        while self.is_running:
            try:
                ready,_,_ = select.select([self.client_socket], [], [], self.timeout)
                # 使用 select 来非阻塞监听
                if ready:
                    response = self.client_socket.recv(1024)
                    # 为什么服务器端关闭后仍然能收到ack---记得清理缓冲区
                    if response:
                        print("上一条信息状态:",end=' ')
                        self.handle_response_from_server(response)
                        # while self.client_socket.recv(1024):
                        #     pass
                        # 清理client的socket的缓冲区
                    else:
                        print("server is shutting down\nconnection has been closed by server")
                        self.is_running = False
                        self.client_socket.close()
                        break
                else:# 超时
                    self.is_running = False
                    print("oops! something goes wrong!!(probably timeout)")
                    self.client_socket.close()
                    break
            except Exception as e:# 运行错误
                self.is_running = False
                print(f"oops! An error occurred: {e}")
                self.client_socket.close()
                break


    def handle_response_from_server(self,reponse):
        '''
        用于处理从服务器返回的信息
        :param reponse:
        :return:
        '''
        print(reponse.decode("utf-8"))

    def send_message(self):
        '''
        用于执行发送信息的函数，用input接收输入(会阻塞)
        :return:
        '''
        while self.is_running:
            try:
                ready,_,_ = select.select([sys.stdin],[],[],1)
                if ready:
                    message = input()

                    # 因为使用input会阻塞，会妨碍client_socket.settimeout()的作用
                    # 考虑用多线程接收数据

                    #注意使用byte object进行数据传输
                    # 客户端要传输的信息怎么获取？

                    self.client_socket.send(message.encode("utf-8"))

                    # 什么时候结束传输--判断条件
                    #
                    # if message=="":
                    #     break
                    # # 不想发了，发送""表示断开
                    # response = self.client_socket.recv(1024)
                    # if response == b'':
                    #     break
                    # 如果收到空字节，表示服务器断开连接
                    # 这个地方有点问题

                    # ACK信息
                    # print("打印相应的response信息:"+response.decode("utf-8"))
            except Exception as e:
                self.is_running = False
                print(f"An error occurred while sending message: {e}")
                break
                # self.client_socket.close()

    def start(self):
        '''
        启动连接，并用一个新线程监听服务器状态，主线程执行发送信息
        :return:
        '''
        self.connect()
        # 多线程，一个用于监听与服务器的连接，一个用于进行收数据
        listener_thread = threading.Thread(target=self.listen_for_server)
        listener_thread.start()
        # 主线程用于和服务器发送信息
        print("输入要传输的数据")
        self.send_message()
        # 等待监听线程结束
        listener_thread.join()


