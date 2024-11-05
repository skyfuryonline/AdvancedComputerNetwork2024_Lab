from Lab1.client.clientUDP import clientUDP


client = clientUDP()
try:
    client.start()
finally:
    client.close()