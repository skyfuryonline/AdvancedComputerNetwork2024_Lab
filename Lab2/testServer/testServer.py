from Lab2.Lab2Server.server import server

server = server()
try:
    server.start()
finally:
    server.broadcastShutdown()
    server.server_socket.close()
