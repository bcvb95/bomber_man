import pygame
import socket
import time
from misc import *

from listener import Listener

IP = "127.0.0.1"
SERVER_PORT = 6873
CLIENT_PORT = 6874

class TestServer(Listener):
    def __init__(self, ip, port, multiple_cons=False, name="Server", verbose=False):
        Listener.__init__(self, ip, port, multiple_cons, name, verbose)
        self.moves = []

    def sendMsg(self, msg, to_ip, to_port):
       self.sendPacket(msg, to_ip, to_port)

    def broadcast_moves(self, to_ip, to_port):
        self.sendMsg("m" + listToStringParser(self.moves), to_ip, to_port)

    def receiveMsg(self, data, addr):
        ack_moves, new_moves = stringToListParser(data, ';')
        self.moves = self.moves + stringToListParser(new_moves, ',')

class Client(Listener):
    def __init__(self, ip, port, serverIP, serverPort, player = None , name="Client", verbose=False):
        Listener.__init__(self, ip, port, name, verbose)
        self.serverIP = serverIP
        self.serverPort = serverPort
        self.latest_move = 0
        self.player = player

        ## added by bjørn 
        self.logged_in = False
        self.username = ""
        self.player_number = None

    def sendMsg(self, msg):
        self.sendPacket(msg, self.serverIP, self.serverPort)

    def receiveMsg(self, data, addr):
        msg_type, data = data[0], data[1:]
        if msg_type == 'l':
            self.handleLoginResponse(data, addr)

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
                if timestamp >= self.latest_move:
                    ack_moves.append(moves[i])
                    self.latest_move = timestamp
                    self.player.do_move(moves[i])

        ack_moves = listToStringParser(ack_moves)
        self.sendMsg("a" + ack_moves + ";" + new_moves)

    ## added by bjørn
    def logIn(self, username):
        if not self.logged_in:
            login_msg = "l%s" % username
            self.sendMsg(login_msg)

    ## added by bjørn
    def handleLoginResponse(self, data, from_addr):
        if from_addr == (self.serverIP, self.serverPort):
            if not self.logged_in: # if not logged in
                # handle login/logout related
                parsed_login = stringToListParser(data, seperator=',')
                login_resp = parsed_login[0] 
                # get login response
                if login_resp == "login_failed":
                    self.logged_in = False
                elif login_resp == "login_success":
                    self.logged_in = True
                    self.username = parsed_login[1]
                    self.player_number = parsed_login[2]
                    print("CLIENT: logged into server with username %s as player number %s" % (self.username, self.player_number))

if __name__ == "__main__":
    pass