from Lab1.server.serverUDP import  serverUDP

server = serverUDP()

try:
    server.start()

finally:
    server.shutdown()