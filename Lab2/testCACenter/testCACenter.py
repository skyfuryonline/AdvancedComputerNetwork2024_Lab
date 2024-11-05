from Lab2.Lab2UDPServer.CACenter import CA

ca = CA()
try:
    ca.start()
except:
    ca.shutdown()