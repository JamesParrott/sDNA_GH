#! python
# https://docs.python.org/3/library/socketserver.html#socketserver-udpserver-example
 
import socket
import time

HOST, PORT = "127.0.0.1", 9999

# SOCK_DGRAM is the socket type to use for UDP sockets
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

words = """ As you can see, there is no connect() call; UDP has no connections.
            Instead, data is directly sent to the recipient via sendto().  """

for word in words.split():
    data = ('%s\n' % word.strip()).encode("utf-8")
    sock.sendto(data, (HOST, PORT))
    time.sleep(0.15)