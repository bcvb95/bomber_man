import pygame
import socket
import time

from listener import Listener

IP = "127.0.0.1"
SERVER_PORT = 6873
CLIENT_PORT = 6874

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