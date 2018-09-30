import pygame
import socket
import time
from misc import *

from packetmanager import PacketManager

class Client(PacketManager):
    def __init__(self, ip, port, serverIP, serverPort, player = None , name="Client", verbose=False):
        PacketManager.__init__(self, ip, port, name, verbose)
        self.serverIP = serverIP
        self.serverPort = serverPort
        self.player = player

        self.server_seq = 0
        self.stalled_packets = []

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

    def handleNewMovesPacket(self, data, forced=False):
        orig_data = data
        data_lst = data.split('>')
        print(data_lst)
        data, seq = data_lst[0], int(data_lst[1])
        if not forced_handle:
            if seq > self.server_seq+1:
                self.stalled_packets.append((orig_data, seq, 0))
                return
            elif seq <= self.server_seq:
                return
            self.server_seq = seq
        ack_moves = []
        if len(data) > 0:
            moves = data.split(':')
            for i in range(len(moves)):
                if len(moves[i][0]) == 0: continue
                ack_moves.append(moves[i])
                self.player.do_move(moves[i])
        new_moves = listToStringParser(self.player.get_moves())
        ack_moves = listToStringParser(ack_moves)
        self.sendMsg("a" + ack_moves + ";" + new_moves)

        for i in range(len(self.stalled_packets)):
            force_handle = self.stalled_packets[i][2] >= STALLED_TOLERANCE
            if self.stalled_packets[i][1] == self.server_seq+1 or force_handle:
                stalled_data = self.stalled_packets[i][0]
                del self.stalled_packets[i]
                self.handleNewMovesPacket(stalled_data, force_handle)
                return
            else:
                self.stalled_packets[i] = (self.stalled_packets[0], stalled_packets[1], stalled_packets[2] + 1)


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