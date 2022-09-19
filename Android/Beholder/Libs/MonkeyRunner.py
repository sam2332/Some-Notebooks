import socket
import subprocess
import sys
from .Beholder import adb

class MonkeyRunner:
    def __init__(self, create_monkey=True):
        self.create_monkey = create_monkey
        self.port = 9905
        self.p = None
        self.s = None

    def __enter__(self):
        if self.p is not None:
            self.p.kill()
        adb(["forward", "--remove-all"])
        command = ["adb", "shell", "monkey", f"--port {self.port}"]
        self.p = shell(command, close_fds=True, returns_POpen=True)
        adb(f"forward tcp:{self.port} tcp:{self.port}")
        time.sleep(0.75)
        self.connect()
        return self

    def connect(self):
        HOST = "127.0.0.1"
        PORT = self.port

        if self.s is not None:
            self.s.close()
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((HOST, PORT))

    def raw(self, s):
        try:
            self.s.sendall(f"{s}\r\n".encode("ascii"))
            # return self.s.recv(10)
        except Exception as e:
            print("raw", e)
            self.connect()
            return self.raw(s)

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if self.create_monkey:
            self.p.kill()
            self.p = None
            if self.s is not None:
                self.s.close()
                self.s = None
            print("Cleaning up")
            shell(["adb", "forward", "--remove-all"])