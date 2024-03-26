#! python3
# https://docs.python.org/3/library/socketserver.html#socketserver-udpserver-example 
import os
import sys
import pathlib
import socketserver
import multiprocessing
import subprocess

from collections import deque



class MyUDPHandler(socketserver.BaseRequestHandler):
    """
    This class works similar to the TCP handler class, except that
    self.request consists of a pair of data and client socket, and since
    there is no connection the client address must be given explicitly
    when sending data back via sendto().
    """

    last_output = deque([], maxlen=300)

    def handle(self):
        data = self.request[0].strip()
        socket = self.request[1]
        output = data.decode('utf-8')
        print(output)
        self.last_output.append(output)
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

    # Test output over UDP to stdout from RhinoPython
    # client_path = pathlib.Path(__file__).parent / 'client.py'
    # subprocess.run(rf'"C:\Program Files\Rhino 8\System\Rhino.exe" /nosplash /runscript="_-RunPythonScript {client_path} _enter _exit _enterend"')

    test_gh_file_path = pathlib.Path(__file__).parent / 'Rhino_8_Read_Geom_(Rhino)_and_Recolour_Objects_test.gh'


    print(rf'Opening: {test_gh_file_path}')
    env = os.environ.copy()
    
    # Exit Rhino afterwards.
    env['SDNA_GH_NON_INTERACTIVE'] = 'True'
    
    # Number of Fuzz tests to run.
    env['SDNA_GH_API_TESTS'] = sys.arg[1] if len(sys.argv) >= 2 else '5'
    
    result = subprocess.run(rf'"C:\Program Files\Rhino 8\System\Rhino.exe" /nosplash /runscript="-_grasshopper _editor _load _document _open {test_gh_file_path}  _enter _exit _enterend"'
                           ,env = env
                           )

    # p.join()

    print(f'{result.returncode=}')
    if result.returncode != 0 or 'SDNA_GH_API_TESTS_FAILED' in ''.join(MyUDPHandler.last_output):
        raise Exception('Error during testing and/or some tests not passed.  Retcode: %s' % result.returncode)


    sys.exit(0)