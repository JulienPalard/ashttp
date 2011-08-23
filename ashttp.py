#!/usr/bin/env python
import ANSI
import pty
import os
import sys
import threading
import BaseHTTPServer
import SocketServer
from fcntl import ioctl
from termios import TIOCSWINSZ
from struct import pack


"""
Please read the README
"""

class Pipe():
    def __init__(self, fd_read, read, fd_write):
        self.fd_read = fd_read
        self.read = read
        self.fd_write = fd_write

class HttpHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def OK(self, data):
        self.wfile.write("HTTP/1.1 200 OK\r\nServer: ashttp\r\nContent-Length:")
        self.wfile.write(str(len(data)))
        self.wfile.write("\r\n\r\n")
        self.wfile.write(data)

    def do_GET(self):
        self.OK(str(self.data_source))

class BackgroundProgramInAPTY():
    def spawn(self, argv):
        if type(argv) == type(''):
            argv = (argv,)
        pid, master_fd = pty.fork()
        if pid == pty.CHILD:
            try:
                os.execlp(argv[0], *argv)
            except Exception as e:
                print e
            sys.exit(0)
        else:
            ioctl(master_fd, TIOCSWINSZ, pack("HHHH", 24, 80, 0, 0))
            return master_fd

    def __init__(self, argv):
        self.ansi = ANSI.ANSI()
        self.master_fd = self.spawn(argv)

    def __call__(self):
        while True:
            try:
                self.ansi.write(os.read(self.master_fd, 1024))
            except (IOError, OSError):
                pass  # Don't whine if the program left ...

    def __str__(self):
        return str(self.ansi)

def main(argc, argv):
    if argc < 3:
        print "USAGE: %s PORT COMMAND ARGS" % argv[0]
        sys.exit(1)
    background_program = BackgroundProgramInAPTY(argv[2:])
    thread = threading.Thread(target=background_program)
    thread.setDaemon(True)
    thread.start()
    HttpHandler.data_source = background_program
    SocketServer.TCPServer.allow_reuse_address = True
    httpd = SocketServer.TCPServer(("", int(argv[1])), HttpHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.shutdown()

if __name__ == "__main__":
    main(len(sys.argv), sys.argv)
