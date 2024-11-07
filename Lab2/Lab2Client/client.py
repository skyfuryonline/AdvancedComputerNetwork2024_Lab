import socket
from time import sleep

import pyDes
from Lab1.client.clientTCP import clientTCP
import base64
from Crypto.Cipher import PKCS1_v1_5
from Crypto.Hash import SHA256
from Crypto.Signature import pkcs1_15
import os.path
from Crypto import Random
from Crypto.PublicKey import RSA
import pyDes
from Crypto.Random import get_random_bytes
import select
import sys
import threading


class client(clientTCP):
    def __init__(self):
        super().__init__()
        # self.des_key = None
        self.des_key_server = None

        # 记录从CA中心请求的电子证书
        self.certificate = None
        # 自己的信息
        self.information = "I am a client from YNU"

        #CA中心的信息
        self.CA = {"host":"127.0.0.1","port":8888}
        self.CA_socket = None

        # 不要反复创建rsa密钥对
        # self.create_rsa_key()
        # 记录自己的des密钥
        # self.create_des_key()
        # 记录自己的公私密钥对
        key = open("../ClientRSAKey/private_pem").read()
        self.private_key = RSA.importKey(key)
        key = open("../ClientRSAKey/public_pem").read()
        self.public_key = RSA.importKey(key)
        # 记录服务器的公私密钥对
        key = open("../ServerRSAKey/private_pem").read()
        self.private_key_server = RSA.importKey(key)
        key = open("../ServerRSAKey/public_pem").read()
        self.public_key_server = RSA.importKey(key)


    def des_encrypt(self,data):
        des = pyDes.des(self.des_key_server, pyDes.CBC, b"\0\0\0\0\0\0\0\0", pad=None, padmode=pyDes.PAD_PKCS5)
        # 使用初始化向量IV来确保每次加密的密文不同，即使相同的明文和密钥被多次使用。IV通常不需要保密，
        # 但必须确保每次加密时都是唯一的或不可预测的，以防止攻击者推测密文模式或明文内容。
        # CBC模式：这种模式需要使用一个初始化向量，它在加密过程中会被用到，因此每个加密操作都需要一个新的IV来保证安全性
        # key:即加密密钥，8个字节
        # des算法针对字节
        encrypted_data = des.encrypt(data)
        return encrypted_data

    def des_decrypt(self,encrypted_data):
        des = pyDes.des(self.des_key_server, pyDes.CBC, b"\0\0\0\0\0\0\0\0", pad=None, padmode=pyDes.PAD_PKCS5)
        decrypted_data = des.decrypt(encrypted_data)
        return decrypted_data

    def rsa_encrypt(self, data, key):
        pk = PKCS1_v1_5.new(key)
        data_base64 = base64.b64encode(data)
        encrypt_data = pk.encrypt(data_base64)
        result = base64.b64encode(encrypt_data)
        return result

    def rsa_decrypt(self, encrypted_data, key):
        # 此处收到的encryped_data是经过base64-rs-base64编码的
        pk = PKCS1_v1_5.new(key)
        decrypt_base64 = base64.b64decode(encrypted_data)
        decrypt_data = pk.decrypt(decrypt_base64, 0)
        return base64.b64decode(decrypt_data)


    def create_rsa_key(self):
        '''
        生成客户端的一对公私密钥,并写入文件中
        :return:
        '''
        random_gen = Random.new().read
        rsa = RSA.generate(1024, random_gen)
        private_pem = rsa.exportKey()
        if not os.path.exists("../ClientRSAKey"):
            os.mkdir("../ClientRSAKey")
        with open('../ClientRSAKey/private_pem', 'wb') as f:
            f.write(private_pem)

        public_pem = rsa.publickey().exportKey()
        with open('../ClientRSAKey/public_pem', 'wb') as f:
            f.write(public_pem)

    # def create_des_key(self):
    #     # 生成8字节的des密钥
    #     self.des_key = get_random_bytes(8)


    # 重写接收服务器数据的函数
    def handle_response_from_server(self,encrypted_response):
        response = self.des_decrypt(encrypted_response)
        print("来自服务器信息为： ",response.decode('utf-8'))

    # 重写发送数据的函数
    def send_message(self):
        while self.is_running:
            try:
                ready,_,_ = select.select([sys.stdin],[],[],1)
                if ready:
                    message = input()
                    # 以下进行数字签名：
                    # 发送者对消息内容进行哈希运算，并使用其私钥对哈希值进行加密，生成签名。这个签名和消息一起发送给接收者。

                    # 对要发送的数据进行base64编码
                    message = base64.b64encode(message.encode('utf-8'))
                    #计算hash并签名----没有使用单独函数实现
                    hash_val =  SHA256.new(message)
                    # 用客户端的私钥签名
                    sign = pkcs1_15.new(self.private_key).sign(hash_val)
                    # 使用des加密要发送的数据
                    encrypt_data = self.des_encrypt(message)
                    # 发送des加密数据和签名
                    self.client_socket.send(encrypt_data)
                    self.client_socket.send(sign)

            except Exception as e:
                self.is_running = False
                print(f"An error occurred while sending message: {e}")
                break

    # 向CA中心发送请求
    def requestCA(self):
        '''
        发送方向CA中心发送个人信息和公钥
        CA把发送方的个人信息和公钥打包在数字证书里
        CA用自己的私钥对数字证书进行签名，再把签名放到证书里
        CA把数字证书发给发送方
        :return:
        '''
        # 采用UDP连接
        self.CA_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        # 发送自己的信息
        self.CA_socket.sendto(self.information.encode(),(self.CA["host"],self.CA["port"]))
        # 发送公钥,把自己公钥的位置发给CA，让CA自己去读取
        loc_public_key = "../ClientRSAKey/public_pem"
        self.CA_socket.sendto(loc_public_key.encode(),(self.CA["host"],self.CA["port"]))

        # 接收CA发送的数字证书
        self.certificate,_ = self.CA_socket.recvfrom(1024)

        # 关闭CA中心的socket
        self.CA_socket.close()
        return

    # 发送方向接收方发送数字证书
    def SendCertificate(self):
        try:
            if self.certificate is not None:
                self.client_socket.send(self.certificate)
            return
        except Exception as e:
            print(f"failed to fetch a certificate: {e}")

    # 重写启动start函数
    def start(self):
        '''
        启动连接，并用一个新线程监听服务器状态，主线程执行发送信息
        :return:
        '''
        self.connect()
        try:
            # 先向CA中心请求数字证书
            self.requestCA()
            # 向接收方发送自己的数字证书
            self.SendCertificate()
        except:
            # 请求证书失败，自行了断
            self.client_socket.close()
            return
        try:
            #接收服务器端的des密钥,用客户端的私钥进行解密
            self.des_key_server = self.rsa_decrypt(self.client_socket.recv(1024),self.private_key)
            assert self.des_key_server!=0
            # 解密失败返回0
        except Exception as e:
            print(f"oops! {e}")
            self.client_socket.close()
            return
        # 多线程，一个用于监听与服务器的连接，一个用于进行收数据
        listener_thread = threading.Thread(target=self.listen_for_server)
        listener_thread.start()
        # 主线程用于和服务器发送信息
        print("输入要传输的数据")
        self.send_message()
        # 等待监听线程结束
        listener_thread.join()