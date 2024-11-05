import sys
import pyDes

def encrypt_data(data, key):
    des = pyDes.des(key,pyDes.CBC,b"\0\0\0\0\0\0\0\0",pad=None,padmode=pyDes.PAD_PKCS5)
    #使用初始化向量IV来确保每次加密的密文不同，即使相同的明文和密钥被多次使用。IV通常不需要保密，
    #但必须确保每次加密时都是唯一的或不可预测的，以防止攻击者推测密文模式或明文内容。
    #CBC模式：这种模式需要使用一个初始化向量，它在加密过程中会被用到，因此每个加密操作都需要一个新的IV来保证安全性
    # key:即加密密钥，8个字节
    # des算法针对字节
    encrypted = des.encrypt(data)
    return encrypted

def decrypt_data(encrypted_data, key):
    des = pyDes.des(key,pyDes.CBC,b"\0\0\0\0\0\0\0\0",pad=None,padmode=pyDes.PAD_PKCS5)
    decrypted_data = des.decrypt(encrypted_data)
    return decrypted_data


if __name__ == "__main__":
    key = b"01234567"
    data = b"hello world"
    encrypted_data = encrypt_data(data, key)
    print("encrypted_data", encrypted_data)

    decrypted_data = decrypt_data(encrypted_data, key)
    print("decrypted_data", decrypted_data)