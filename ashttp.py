#!/usr/bin/env python
import os
import sys
import threading
try:
    import ANSI
except ImportError:
    print "Please install python-pexpect"
    sys.exit(1)
import pty
import BaseHTTPServer
import SocketServer
from fcntl import ioctl
from termios import TIOCSWINSZ
from struct import pack
try:
    from argparse import ArgumentParser
except ImportError:
    print "Please install python-argparse"
    sys.exit(1)


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
    def __init__(self, command, argv=[], width=80, height=24):
        self.ansi = ANSI.ANSI(height, width)
        self.width = width
        self.height = height
        self.master_fd = self.spawn([command] + argv)

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
            ioctl(master_fd, TIOCSWINSZ, pack("HHHH",
                                              self.height, self.width,
                                              0, 0))
            return master_fd

    def __call__(self):
        while True:
            try:
                self.ansi.write(os.read(self.master_fd, 1024))
            except (IOError, OSError):
                pass  # Don't whine if the program left ...

    def __str__(self):
        return str(self.ansi)

def ashttp(args):
    background_program = BackgroundProgramInAPTY(args.command,
                                                 args.args,
                                                 args.width,
                                                 args.height)
    thread = threading.Thread(target=background_program)
    thread.setDaemon(True)
    thread.start()
    HttpHandler.data_source = background_program
    SocketServer.TCPServer.allow_reuse_address = True
    httpd = SocketServer.TCPServer(("", args.port), HttpHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.shutdown()


def main(argc, argv):
    parser = ArgumentParser(
        description="Display a text program (like top, ...) over http.",
        epilog="""
If an argument of you command begin with -, use a double dash
to separate your program arguments from ashttp arguments, like :
ashttp -- watch -n 1 ls /tmp""")
    parser.add_argument("-p", "--port", dest="port", default=8080,
                        metavar=8080, type=int,
                        help="Port to listen for HTTP requests")
    parser.add_argument("-W", "--width", type=int,
                        dest="width", default=80, metavar=80,
                        help="Width of the emulated terminal")
    parser.add_argument("-H", "--height", type=int,
                      dest="height", default=24, metavar=24,
                      help="Height of the emulated terminal")
    parser.add_argument("command",
                      help="Command to run and serve")
    parser.add_argument('args', metavar='ARG', type=str, nargs='*', default=[],
                        help='Arguments that are given to the command.')
    ashttp(parser.parse_args())

if __name__ == "__main__":
    main(len(sys.argv), sys.argv)
