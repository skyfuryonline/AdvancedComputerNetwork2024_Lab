from Lab1.server.serverTCP import serverTCP

server = serverTCP()
try:
    server.start()
finally:
    server.broadcastShutdown()
    server.server_socket.close()

