import os.path

from Crypto import Random
from Crypto.PublicKey import RSA
import base64
from Crypto.Cipher import PKCS1_v1_5
from Crypto.Hash import SHA

def create_rsa_key():
    random_gen = Random.new().read

    rsa = RSA.generate(1024, random_gen)

    private_pem = rsa.exportKey()
    if not os.path.exists("RSAkeyTest"):
        os.mkdir("RSAkeyTest")
    with open('RSAkeyTest/private_pem', 'wb') as f:
        f.write(private_pem)

    public_pem = rsa.publickey().exportKey()
    with open('RSAkeyTest/public_pem', 'wb') as f:
        f.write(public_pem)


# 公钥加密
def encrypt(msg):
    '''
    :param msg:需要加密的明文文本，公钥加密，私钥解密
    :return:
    '''
    key = open('RSAkeyTest/public_pem').read()
    publickey = RSA.importKey(key)

    pk = PKCS1_v1_5.new(publickey)
    encrypt_text = pk.encrypt(msg.encode('utf-8'))

    result = base64.b64encode(encrypt_text)
    return result

# 私钥解密
def decrypt(msg):
    '''
    :param msg:加密的密文
    :return:
    '''
    key = open('RSAkeyTest/private_pem').read()
    privatekey = RSA.importKey(key)
    pk = PKCS1_v1_5.new(privatekey)
    encrypt_text = base64.b64decode(msg)
    decrypt_text = pk.decrypt(encrypt_text,0)
    # 注意还有一个sentinel参数
    return decrypt_text.decode('utf-8')

if __name__ == '__main__':
    create_rsa_key()
    msg = "这是一条测试信息"
    encrypt_text = encrypt(msg)
    print("加密信息是：",encrypt_text.decode("utf-8"))
    print("解密信息是：",decrypt(encrypt_text))





