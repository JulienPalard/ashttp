#!/usr/bin/env python
import sys
import threading
import logtop
import BaseHTTPServer
import SocketServer
from argparse import ArgumentParser  # apt-get install python-argparse
from subprocess import Popen, PIPE
import json


class HttpHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def OK(self, data):
        self.wfile.write("HTTP/1.1 200 OK\r\nServer: ashttp\r\nContent-Length:")
        self.wfile.write(str(len(data)))
        self.wfile.write("\r\n\r\n")
        self.wfile.write(data)

    def do_GET(self):
        self.OK(str(self.data_source))


class BackgroundProgramToLogtop():
    def __init__(self, command, json):
        self.program_to_listen = Popen(command, shell=True, stdout=PIPE)
        self.logtop = logtop.logtop(1000)
        self.json = json

    def __call__(self):
        for line in self.program_to_listen.stdout:
            self.logtop.feed(line[:-1])

    def __str__(self):
        if self.json:
            return json.dumps(self.logtop.get(20))
        else:
            return "\x1E".join(['\x1F'.join([str(x) for x in line]) for line in self.logtop.get(20)['lines']])


def logtop_as_http(args):
    background_program = BackgroundProgramToLogtop(args.command, args.json)

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
    thread.join()

if __name__ == "__main__":
    parser = ArgumentParser(
        description="Expose the 'logtop' of a command using HTTP.")
    parser.add_argument("-p", "--port", dest="port", default=8060,
                        metavar=8060, type=int,
                        help="Port to listen for HTTP requests")
    parser.add_argument("-j", "--json", default=False,
                        action="store_true",
                        help="Give stats using json format.")
    parser.add_argument("command",
                      help="Command to run and serve, "
                        "excuted in an 'sh -c' so you may use pipes, etc... ")
    logtop_as_http(parser.parse_args())
