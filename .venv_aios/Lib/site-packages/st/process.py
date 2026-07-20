import sys
import threading
import subprocess
import multiprocessing


def process(target, args=(), finished=None):
    p = multiprocessing.Process(target=target, args=args)
    p.start()

    def check_finished():
        p.join()
        finished()

    threading.Thread(target=check_finished).start()


class Process:
    def __init__(self, cmd):
        self.p = subprocess.Popen(cmd,
                                  shell=False,
                                  creationflags=0x00000008 if sys.platform == "win32" else 0,
                                  stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE)

    def write_line(self, line: str):
        self.p.stdin.write(line.encode())
        self.p.stdin.write('\n'.encode())
        self.p.stdin.flush()

    def read_line(self) -> str:
        return self.p.stdout.readline().decode().replace('\r\n', '').replace('\n', '')

    def read_until(self, until):
        lines = []

        while True:
            line = self.read_line()
            if line == until:
                return '\n'.join(lines)
            elif not line:
                break
            else:
                lines.append(line)
