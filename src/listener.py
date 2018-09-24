import socket
import select
import time
from multiprocessing import Process, Lock, Pipe

TIMEOUT = 0.1

class Listener(object):
    def __init__(self, ip, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setblocking(0)
        self.ip = ip
        self.port = port
        self.sock.bind((self.ip, self.port))
        self.lock = Lock()
        self.pipe_parentEnd, self.pipe_childEnd = Pipe()
        self.listen_process = None

    def receiveMsg(self, data, from_addr):
        print("received: %s" % data)

    def listen(self):
        self.listen_process = Process(target=self._listen_thread)
        self.listen_process.start()

    def stop_listen(self):
        self.pipe_parentEnd.send("stop")
        self.lock.acquire()
        self.listen_process.join()
        self.lock.release()

    def _listen_thread(self):
        while 1:
            if self.pipe_childEnd.poll():
                msg = self.pipe_childEnd.recv()
                if msg == "stop":
                    return
            self.lock.acquire()
            ready = select.select([self.sock], [], [], TIMEOUT)
            if ready[0]:
                data, addr = self.sock.recvfrom(4096)
                self.receiveMsg(data.decode(), addr)
            self.lock.release()
