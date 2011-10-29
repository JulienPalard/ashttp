#!/usr/bin/env python
import time
import os
import sys
import threading
try:
    import hl_vt100
except ImportError:
    print "Please install hl_vt100 : "
    print " -> https://github.com/JulienPalard/vt100-emulator"
    sys.exit(1)
import BaseHTTPServer
import SocketServer
try:
    from argparse import ArgumentParser
except ImportError:
    print "Please install python-argparse"
    sys.exit(1)


"""
Please read the README
"""

class HttpHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def OK(self, data):
        self.wfile.write("HTTP/1.1 200 OK\r\nServer: ashttp\r\nContent-Length:")
        self.wfile.write(str(len(data)))
        self.wfile.write("\r\n\r\n")
        self.wfile.write(data)

    def do_GET(self):
        self.OK(str(self.data_source))


class BackgroundProgramInAPTY():
    def __init__(self, command, argv=[]):
        self.vt100 = hl_vt100.vt100_headless()
        self.vt100.fork(command, [command] + argv)

    def __call__(self):
        self.vt100.main_loop()

    def __str__(self):
        return "\n".join(self.vt100.getlines())


def ashttp(args):
    background_program = BackgroundProgramInAPTY(args.command, args.args)

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
    background_program.vt100.stop()
    thread.join()

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
    parser.add_argument("command",
                      help="Command to run and serve")
    parser.add_argument('args', metavar='ARG', type=str, nargs='*', default=[],
                        help='Arguments that are given to the command.')
    ashttp(parser.parse_args())

if __name__ == "__main__":
    main(len(sys.argv), sys.argv)
