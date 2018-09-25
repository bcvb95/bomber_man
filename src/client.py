import pygame
import socket
import time
from misc import *

from listener import Listener

IP = "127.0.0.1"
SERVER_PORT = 6873
CLIENT_PORT = 6874

class TestServer(Listener):
    def __init__(self, ip, port, player):
        Listener.__init__(self, ip, port)
        self.player = player
        self.moves = []

    def sendMsg(self, msg, to_ip, to_port):
       self._sendMsg(msg, to_ip, to_port)

    def broadcast_moves(self, to_ip, to_port):
        self.sendMsg("m" + listToStringParser(self.moves), to_ip, to_port)

    def receiveMsg(self, data, addr):
        ack_moves, new_moves = stringToListParser(data, ';')
        self.moves = self.moves + stringToListParser(new_moves, ',')

class Client(Listener):
    def __init__(self, ip, port, serverIP, serverPort, player):
        Listener.__init__(self, ip, port)
        self.serverIP = serverIP
        self.serverPort = serverPort
        self.player = player
        self.latest_move = 0

    def sendMsg(self, msg):
        self._sendMsg(msg, self.serverIP, self.serverPort)
        #self.sock.sendto(msg.encode(), (self.serverIP, self.serverPort))

    def receiveMsg(self, data, addr):
        msg_type, data = data[0], data[1:]
        if msg_type == 'm': # new moves
            self.handleNewMovesPacket(data)

    def handleNewMovesPacket(self, data):
        ack_moves = []
        new_moves = listToStringParser(self.player.get_moves())
        if len(data) > 0:
            moves = sorted([(x, x.split(':')[-1]) for x in stringToListParser(data)], key=lambda x: x[1])
            for i in range(len(moves)):
                if len(moves[i][0]) == 0: continue
                timestamp = int(moves[i][1])
                moves[i] = moves[i][0].strip()
                if timestamp > self.latest_move:
                    ack_moves.append(moves[i])
                    self.latest_move = timestamp
                    self.player.do_move(moves[i])

        ack_moves = listToStringParser(ack_moves)
        self.sendMsg("a" + ack_moves + ";" + new_moves)


class Player(object):
    def __init__(self, id):
        self.id = id
        self.new_moves = []

    def make_move(self, move):
        self.new_moves.append("m%d:%s:%d" % (self.id, move, timeInMs()))

    def get_moves(self):
        moves = self.new_moves
        self.new_moves = []
        return moves

    def do_move(self, move):
        move_list = stringToListParser(move, ':')
        print("Move by: %s\nMove: %s\nTime: %s" % (move_list[0], move_list[1], move_list[2]))

def test_client():
    player1 = Player(1)
    player2 = Player(2)
    server = TestServer("127.0.0.1", SERVER_PORT, player1)
    client = Client("127.0.0.1", CLIENT_PORT, "127.0.0.1", SERVER_PORT, player2)
    server.listen()
    client.listen()
    client.player.make_move('r')
    time.sleep(0.1)
    server.broadcast_moves("127.0.0.1", CLIENT_PORT)
    time.sleep(0.1)
    server.broadcast_moves("127.0.0.1", CLIENT_PORT)
    time.sleep(0.1)
    server.broadcast_moves("127.0.0.1", CLIENT_PORT)
    time.sleep(0.1)
    server.kill()
    client.kill()

if __name__ == "__main__":
    test_client()