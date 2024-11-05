from Lab2.Lab2Client.client import client

client = client()
try:
    client.start()
finally:
    client.client_socket.close()