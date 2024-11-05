from Lab1.client.clientTCP import clientTCP

client = clientTCP()
try:
    client.start()
finally:
    client.client_socket.close()