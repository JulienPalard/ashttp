#!/usr/bin/env python
import ANSI
import pty
import os
import sys

"""
Please read the README
"""

ansi = ANSI.ANSI()

def master_read(fd):
    ansi.write(os.read(fd, 1024))
    return ''

def slave_read(fd):
    data = os.read(fd, 1)
    print ansi.pretty()
    return data

def spawn(argv, master_read=master_read, stdin_read=slave_read):
    """Create a spawned process."""
    if type(argv) == type(''):
        argv = (argv,)
    pid, master_fd = pty.fork()
    if pid == pty.CHILD:
        os.execlp(argv[0], *argv) # , {'TERM': 'vt100'})
        try:
            mode = tty.tcgetattr(STDIN_FILENO)
            tty.setraw(STDIN_FILENO)
        except tty.error:    # This is the same as termios.error
            pass
    pty._copy(master_fd, master_read, stdin_read)
    os.close(master_fd)

def main():
    spawn(sys.argv[1:], master_read, slave_read)
    while True:
        os.read(1, 1)
        print ansi.pretty()
if __name__ == "__main__":
    main()
