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

    def sendMsg(self, msg, to_ip, to_port):
        self.sock.sendto(msg.encode(), (to_ip, to_port))

    def receiveMsg(self, data, addr):
        print("SERVER received: %s" % data)


class Client(Listener):
    def __init__(self, ip, port, serverIP, serverPort):
        Listener.__init__(self, ip, port)
        self.serverIP = serverIP
        self.serverPort = serverPort

    def sendMsg(self, msg):
        self.sock.sendto(msg.encode(), (self.serverIP, self.serverPort))

    def receiveMsg(self, data, addr):
        print("CLIENT received: %s" % data)

def test_client():
    server = TestServer("127.0.0.1", SERVER_PORT)
    client = Client("127.0.0.1", CLIENT_PORT, "127.0.0.1", SERVER_PORT)
    server.listen()
    client.listen()
    client.sendMsg("lol")
    server.sendMsg("hej", "127.0.0.1", SERVER_PORT)
    server.sendMsg("YUP", "127.0.0.1", CLIENT_PORT)
    time.sleep(1)
    server.kill()
    client.kill()

if __name__ == "__main__":
    test_client()