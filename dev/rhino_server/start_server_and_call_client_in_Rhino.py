#! python3
# https://docs.python.org/3/library/socketserver.html#socketserver-udpserver-example 

import pathlib
import socketserver
import multiprocessing
import subprocess

def f(name):
    print('hello', name)


class MyUDPHandler(socketserver.BaseRequestHandler):
    """
    This class works similar to the TCP handler class, except that
    self.request consists of a pair of data and client socket, and since
    there is no connection the client address must be given explicitly
    when sending data back via sendto().
    """

    def handle(self):
        data = self.request[0].strip()
        socket = self.request[1]
        print(f'{self.client_address[0]} wrote {data}')
        socket.sendto(data.upper(), self.client_address)

def start_UDP_server():
    HOST, PORT = "127.0.0.1", 9999
    with socketserver.UDPServer((HOST, PORT), MyUDPHandler) as server:
        server.serve_forever()


if __name__ == '__main__':
    p = multiprocessing.Process(target=start_UDP_server)
    p.daemon = True
    p.start()

    client_path = pathlib.Path(__file__).parent / 'client.py'

    subprocess.run(rf'"C:\Program Files\Rhino 8\System\Rhino.exe" /nosplash /runscript="_-RunPythonScript {client_path} _enter _exit _enterend"')

    p.join()