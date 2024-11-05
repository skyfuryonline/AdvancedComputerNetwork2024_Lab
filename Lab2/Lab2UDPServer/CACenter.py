from Lab1.server.serverUDP import serverUDP
from Crypto import Random
from Crypto.PublicKey import RSA
import os
import base64
from Crypto.Hash import SHA256
from Crypto.Signature import pkcs1_15
import pickle

class CA(serverUDP):
    def __init__(self):
        super().__init__()

        # 不要反复创建rsa密钥对
        # self.create_rsa_key()

        # 记录自己的公私钥对
        key = open("../CARSAKey/private_pem").read()
        self.CA_private_key = RSA.importKey(key)
        key = open("../CARSAKey/public_pem").read()
        self.CA_public_key = RSA.importKey(key)


    def create_rsa_key(self):
        random_gen = Random.new().read
        rsa = RSA.generate(1024, random_gen)
        private_pem = rsa.exportKey()
        if not os.path.exists("../CARSAKey"):
            os.mkdir("../CARSAKey")
        with open('../CARSAKey/private_pem', 'wb') as f:
            f.write(private_pem)

        public_pem = rsa.publickey().exportKey()
        with open('../CARSAKey/public_pem', 'wb') as f:
            f.write(public_pem)

    # 检查请求的发起者是否合法
    def checkLegality(self,request):
        return "YNU" in request

    # 对数字证书签名
    def signCertificate(self,certificate):
        # 考虑先把certificate(元组转换为字节)
        certificate_byte = pickle.dumps(certificate)

        base64_data = base64.b64encode(certificate_byte)
        # 用SHA256计算hash
        hash_val = SHA256.new(base64_data)
        # 用私钥对hash进行签名并对签名进行Base64编码，以便传输,返回签名和数据
        return base64.b64encode(pkcs1_15.new(self.CA_private_key).sign(hash_val))

    # 生成数字证书
    def generateCertificate(self,information,public_key):
        return information,public_key

    def listen(self):
        print("-------------CA center now online-------------")
        while True:
            # 接收发送方的请求,先接收信息数据，再接收公钥的位置
            # 请求信息也可能是接收方发起的，请求CA公钥
            information,client_address = self.server_socket.recvfrom(1024)

            if "public key" in information.decode():
                # 把自己的公钥的位置告诉请求者
                self.server_socket.sendto('../CARSAKey/public_pem'.encode(),client_address)
                continue

            loc_public_key, client_address = self.server_socket.recvfrom(1024)

            # 如果请求发起者不合法，则忽略
            if not self.checkLegality(information.decode()):
                continue

            # CA将请求发起者的信息和公钥地址打包进数字证书---元组类型
            certificate = self.generateCertificate(information,loc_public_key)
            # CA用自己的私钥对数字证书进行签名
            sign = self.signCertificate(certificate)
            # 把数字签名放证书里--又是元组类型
            certificate = (certificate,sign)
            # CA将证书发给请求发起者
            # 怎么把元组转换为bytes？-------------
            certificate_byte = pickle.dumps(certificate)
            self.server_socket.sendto(certificate_byte,client_address)