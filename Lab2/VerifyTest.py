from Crypto import Random
from Crypto.PublicKey import RSA
import base64
from Crypto.Cipher import PKCS1_v1_5
from Crypto.Hash import SHA



def verify(data,sign):
    '''
    :param data:明文数据，签名之前的数据
    :param sign:接收到的sign签名
    :return:
    '''
    data = base64.b64decode(sign)

    key = open('public.pem').read()
    rsakey = RSA.importKey(key)
    sha_name = SHA.new(sign.encode('utf-8'))
    signer = PKCS1_v1_5.new(rsakey)
    res = signer.verify(sha_name, sign)

    return res




if __name__ == '__main__':
    data = "CoCo"
    sign = "签名数据怎么获得阿啊阿啊阿啊阿啊阿啊阿啊阿啊阿啊"
    print(verify(data,sign))