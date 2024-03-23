#! python3
# https://docs.python.org/3/library/socketserver.html#socketserver-udpserver-example 

import pathlib
import socketserver
import multiprocessing
import subprocess



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
        print(data.decode('utf-8'))
        # socket.sendto(data.upper(), self.client_address)

def start_UDP_server():
    HOST, PORT = "127.0.0.1", 9999
    with socketserver.UDPServer((HOST, PORT), MyUDPHandler) as server:
        server.serve_forever()


if __name__ == '__main__':
    p = multiprocessing.Process(target=start_UDP_server)
    p.daemon = True
    print('Starting output printing UDP server.  Press Ctrl+C to quit.')
    p.start()

    test_gh_file_path = pathlib.Path(__file__).parent / 'Rhino_8_Read_Geom_(Rhino)_and_Recolour_Objects_test.gh'
    # test_gh_file_path = 'Rhino_8_Read_Geom_(Rhino)_and_Recolour_Objects_test.gh'

    client_path = pathlib.Path(__file__).parent / 'client.py'
    print(rf'{test_gh_file_path}')
    # subprocess.run(rf'"C:\Program Files\Rhino 8\System\Rhino.exe" /nosplash /runscript="_-RunPythonScript {client_path} _enter _exit _enterend"')
    print(rf'"C:\Program Files\Rhino 8\System\Rhino.exe" /nosplash /runscript="-_grasshopper _editor _load _document _open {test_gh_file_path} _enterend"')
                #   ,env = {'SDNA_GH_NON_INTERACTIVE' : 'True'}
                #   )

    p.join()