import pygame
import socket
import select
import time
from multiprocessing import Process, Lock, Pipe

IP = "127.0.0.1"
SERVER_PORT = 6873
CLIENT_PORT = 6874

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

    def receiveMsg(self, data):
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
                self.receiveMsg(data.decode())
            self.lock.release()

class TestServer(Listener):
    def __init__(self, ip, port):
        Listener.__init__(self, ip, port)

    def sendMsg(self, msg):
        self.sock.sendto(msg.encode(), (self.ip, self.port))

    def receiveMsg(self, data):
        print("SERVER received: %s" % data)

class Client(Listener):
    def __init__(self, ip, port):
        Listener.__init__(self, ip, port)

    def sendMsg(self, msg):
        self.sock.sendto(msg.encode(), (self.ip, self.port))

    def receiveMsg(self, data):
        print("CLIENT received: %s" % data)




def test_client():
    server = TestServer("127.0.0.1", SERVER_PORT)
    server.listen()
    client = Client("127.0.0.1", CLIENT_PORT)
    client.listen()
    client.sendMsg("lol")
    time.sleep(1)
    client.sendMsg("hej")
    time.sleep(1)
    server.sendMsg("YUP")
    time.sleep(1)
    server.stop_listen()
    client.stop_listen()

if __name__ == "__main__":
    test_client()