import base64
from Crypto.Cipher import PKCS1_v1_5
# 用于rsa加密的是大写
from Crypto.Hash import SHA256
from Crypto.Signature import pkcs1_15
# 用于签名的是小写

from Lab1.server.serverTCP import serverTCP
import os.path
from Crypto import Random
from Crypto.PublicKey import RSA
import pyDes
from Crypto.Random import get_random_bytes

import socket
import pickle

class server(serverTCP):
    def __init__(self):
        super().__init__()
        self.des_key = None
        # self.des_key_client = None

        # 不要反复创建rsa密钥对
        # self.create_rsa_key()
        # 记录自己的des密钥
        self.create_des_key()
        # 记录自己的公私密钥对
        key = open("../ServerRSAKey/private_pem").read()
        self.private_key_server = RSA.importKey(key)
        key = open("../ServerRSAKey/public_pem").read()
        self.public_key_server = RSA.importKey(key)

        # 记录客户端的公私密钥对
        key = open("../ClientRSAKey/private_pem").read()
        self.private_key_client = RSA.importKey(key)
        key = open("../ClientRSAKey/public_pem").read()
        self.public_key_client = RSA.importKey(key)

        # 记录CA的公钥
        self.CA_public_key = None
        # 记录与CA的连接信息
        self.CA = {"host": "127.0.0.1", "port": 8888}
        self.CA_socket = None

    def create_rsa_key(self):
        '''
        生成服务器的一对公私密钥,并写入文件中
        :return:
        '''
        random_gen = Random.new().read
        rsa = RSA.generate(1024, random_gen)
        private_pem = rsa.exportKey()
        if not os.path.exists("../ServerRSAKey"):
            os.mkdir("../ServerRSAKey")
        with open('../ServerRSAKey/private_pem', 'wb') as f:
            f.write(private_pem)

        public_pem = rsa.publickey().exportKey()
        with open('../ServerRSAKey/public_pem', 'wb') as f:
            f.write(public_pem)

    def create_des_key(self):
        # 生成8字节的des密钥
        self.des_key = get_random_bytes(8)

    def des_decrypt(self,encrypted_data):
        '''
        用des密钥对密文进行解密，des密钥由客户端用服务器端的rsa公钥加密
        :param encrypted_data: 传入的是经过des加密的密文
        :return: 返回解密的数据
        '''
        des = pyDes.des(self.des_key, pyDes.CBC, b"\0\0\0\0\0\0\0\0", pad=None, padmode=pyDes.PAD_PKCS5)
        decrypted_data = des.decrypt(encrypted_data)
        return decrypted_data

    def des_encrypt(self,data):
        '''
        用des密钥对明文进行加密
        :param data:
        :return:
        '''
        des = pyDes.des(self.des_key,pyDes.CBC,b"\0\0\0\0\0\0\0\0", pad=None, padmode=pyDes.PAD_PKCS5)
        encrypted_data = des.encrypt(data)
        return encrypted_data

    def rsa_encrypt(self,data,key):
        pk  = PKCS1_v1_5.new(key)
        # 此处的data需要base64编码？
        data_base64 = base64.b64encode(data)
        encrypt_data = pk.encrypt(data_base64)
        result = base64.b64encode(encrypt_data)
        return result

    def rsa_decrypt(self,encrypted_data,key):
        pk = PKCS1_v1_5.new(key)
        decrypt_base64 =  base64.b64decode(encrypted_data)
        decrypt_data = pk.decrypt(decrypt_base64,0)
        return base64.b64decode(decrypt_data)

    def sign_data(self,data):
        '''
        对数据进行base64编码，并用服务器端自己的私钥进行签名
        传输数据和签名前均进行base64编码
        :param data:待处理的数据
        :return:tuple(签名，base64编码的数据)
        '''
        # 用base64进行转码
        base64_data = base64.b64encode(data)
        # 用SHA256计算hash
        hash_val = SHA256.new(base64_data)

        # 用私钥对hash进行签名并对签名进行Base64编码，以便传输,返回签名和数据
        return base64.b64encode(pkcs1_15.new(self.private_key_server).sign(hash_val)),base64_data


    def verify_certificate(self,client_certificate):
        '''
        验证客户端证书(从CA中心领取CA公钥)
        同时需要考虑怎么预处理接收到的certificate
        :param client_certificate:
        :return:
        '''
        # 采用UDP连接
        self.CA_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 向CA发送公钥请求
        self.CA_socket.sendto("request public key".encode(),(self.CA["host"],self.CA["port"]))
        # 接收CA公钥的位置
        self.CA_public_key,_ = self.CA_socket.recvfrom(1024)
        # 读取CA公钥
        self.CA_public_key =RSA.importKey(open(self.CA_public_key).read())

        # 用公钥对数字证书解密并验证---要用pickle还原数据
        # tuple(information,loc_public_key)->sign(tuple)->(tuple,sign)->pickle(...)
        # 拿到签名和数字证书（元组类型）
        certificate,sign_base64 = pickle.loads(client_certificate)
        sign = base64.b64decode(sign_base64)
        # 此时再用CA的公钥对certificate进行验证即可
        pk = pkcs1_15.new(self.CA_public_key)
        certificate_byte = pickle.dumps(certificate)
        base64_data = base64.b64encode(certificate_byte)
        hash_val = SHA256.new(base64_data)
        try:
            pk.verify(hash_val, sign)
            # 如果没有引发异常，则意味着通过检验
            return True
        except:
            return False

    # 重写处理客户端请求的部分
    def handle_client(self, client_socket,client_address):
        # 接收客户端发送的数字证书
        client_certificate = client_socket.recv(1024)
        # 此处应该验证客户端的证书，如果没通过，直接关闭与客户端的连接，就不进入下面的部分了
        if not self.verify_certificate(client_certificate):
            client_socket.close()
            return

        # 用客户端的公钥加密des密钥，用base64编码，并发送
        # 先对内容用base64编码，再对加密结果再次编码
        des_key_encrypted = self.rsa_encrypt(self.des_key,self.public_key_client)
        client_socket.send(des_key_encrypted)

        while True:
            try:
                # 接收到的信息应该是经过des加密的数据和签名
                encrypt_data = client_socket.recv(1024)
                # 接收客户端的签名
                signature = client_socket.recv(1024)
                if encrypt_data==b"":
                    break
                # 断开连接的时候message为""
                print(f"从IP：{client_address[0]} Port: {client_address[1]} 处接受到的信息: ",end='')

                # 处理接收到的数据
                self.handle_data(encrypt_data,signature)

                response = "ACK"
                client_socket.send(self.des_encrypt(response.encode()))
            except ConnectionResetError:
                print("oops!! something goes wrong!")
                break

        client_socket.close()
        self.client.remove(client_socket)
        # 断开连接时从列表中移除对应的socket
        print(f"------------------从IP：{client_address[0]} Port: {client_address[1]} 处断开连接------------------")

    # 接收数据、密钥、签名，检验签名是否正确
    def verify(self,data,key,sign):
        '''
        接收者使用发送者的公钥来验证签名:
        生成哈希值：接收者对接收到的消息内容再次进行哈希运算，得到消息摘要。
        解密签名：使用发送者的公钥解密签名，得到发送者加密的哈希值
        比较哈希值：如果解密得到的哈希值和接收者自己计算的哈希值一致，验证成功；否则，验证失败，说明消息可能被篡改或签名无效。
        :param data:
        :param key:
        :param sign:
        :return:
        '''
        pk = pkcs1_15.new(key)
        try:
            data_hash = SHA256.new(base64.b64encode(data.encode('utf-8')))
            pk.verify(data_hash,sign)
            # 如果没有引发异常，则意味着通过检验
            print(data)
        except (ValueError, TypeError):
            print("warning! data has been change !")



    # 处理接收客户端信息的部分,不是重写，接收加密数据和数字签名
    def handle_data(self,encrypt_data,sign):
        # 收到的数据应该是：data+sign
        # message=input().endcode(utf-8)->base64(message)+H(message)->sign(H)+des(base)
        decrypt_data = self.des_decrypt(encrypt_data)
        base64_decode_data = base64.b64decode(decrypt_data)
        message = base64_decode_data.decode("utf-8")

        #用客户端的公钥检验，如果检验通过，则直接打印数据
        self.verify(message,self.public_key_client,sign)


