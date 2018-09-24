import pygame
import socket

from listener import Listener

IP="127.0.0.1"
PORT=8338

P_SIZE=256


class TestServer(Listener):
    def __init__(self, ip, port):
        Listener.__init__(self, ip, port)

    def sendMsg(self, msg):
        self.sock.sendto(msg.encode(), (self.ip, self.port))

    def receiveMsg(self, data):
        print("SERVER received: %s" % data)

def test_server():
    server = TestServer(IP,PORT)



if __name__ == "__main__":
    test_server()