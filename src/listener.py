import socket
import select
import time
from threading import Thread, Lock

TIMEOUT = 0.1

class Listener(object):
    def __init__(self, ip, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setblocking(0)
        self.ip = ip
        self.port = port
        self.sock.bind((self.ip, self.port))
        self.lock = Lock()
        self.listen_thread = None
        self.kill = False

    def receiveMsg(self, data):
        print("received: %s" % data)

    def listen(self):
        self.listen_thread = Thread(target=self._listen_thread)
        self.listen_thread.start()

    def stop_listen(self):
        self.lock.acquire()
        self.kill = True
        self.lock.release()
        self.listen_thread.join()

    def _listen_thread(self):
        while 1:
            time.sleep(0.0001)
            self.lock.acquire()
            if self.kill:
                return
            ready = select.select([self.sock], [], [], TIMEOUT)
            if ready[0]:
                data, addr = self.sock.recvfrom(4096)
                self.receiveMsg([data.decode()])
            self.lock.release()
