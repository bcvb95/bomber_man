import pygame
import socket
import time
from misc import *

from packetmanager import PacketManager

STALLED_TOLERANCE = 10

class Client(PacketManager):
    def __init__(self, ip, port, serverIP, serverPort, player = None , name="Client",logfile=None,  verbose=False):
        PacketManager.__init__(self, ip, port, name, logfile=logfile, verbose=verbose)
        self.serverIP = serverIP
        self.serverPort = serverPort
        self.latest_move = 0
        self.player = player

        self.server_seq = -1
        self.stalled_packets = []

        ## added by bjørn
        self.logged_in = False
        self.username = ""
        self.player_number = None

        self.is_host = False

    def sendMsg(self, msg):
        self.sendPacket(msg, self.serverIP, self.serverPort)

    def receiveMsg(self, data, addr, forced=False):
        orig_data = data
        msg_type, data = data[0], data[1:]
        data_lst = data.split('>')

        data, seq = data_lst[0].strip(), int(data_lst[1].strip())
        if msg_type == 's':
            print(seq, self.server_seq)
        if not forced:
            if seq > self.server_seq+1:
                self.stalled_packets.append((orig_data, addr, seq, 0))
                return
            elif seq <= self.server_seq:
                return
            self.server_seq = seq

        if msg_type == 'l':
            self.handleLoginResponse(data, addr)
        elif msg_type == 's':
            print("client new board: %s" % data)
            self.handleBoardSync(data)
        elif msg_type == 'u':
            self.sendSyncBoard()

        elif msg_type == 'm': # new moves
            self.handleNewMovesPacket(data)

        if forced:
            return
        for i in range(len(self.stalled_packets)):
            if self.verbose: self.log("stalling packet")
            force_handle = self.stalled_packets[i][3] >= STALLED_TOLERANCE
            if self.stalled_packets[i][2] == self.server_seq+1 or force_handle:
                stalled_data, from_addr = self.stalled_packets[i][0], self.stalled_packets[i][1]
                del self.stalled_packets[i]
                self.receiveMsg(stalled_data, from_addr, force_handle)
                return
            else:
                self.stalled_packets[i] = (self.stalled_packets[i][0], self.stalled_packets[i][1], self.stalled_packets[i][2], self.stalled_packets[i][3] + 1)


    def handleNewMovesPacket(self, data):
        ack_moves = []
        if len(data) > 0:
            moves = data.split(',')
            for i in range(len(moves)):
                if len(moves[i][0]) == 0: continue
                ack_moves.append(moves[i])
                self.player.do_move(moves[i])
        new_moves = listToStringParser(self.player.get_moves())
        ack_moves = listToStringParser(ack_moves)
        self.sendMsg("a" + ack_moves + ";" + new_moves)

    def handleBoardSync(self, data):
        print("CLIENT: handling board sync!")
        for i in range(len(self.player.colorgrid.grid_rects)):
            self.player.colorgrid.grid_rects[i] = (int(data[i])-1, self.player.colorgrid.grid_rects[i][1])

    def sendSyncBoard(self):
        print("CLIENT: sending synced board")
        msg = "u"
        for rect in self.player.colorgrid.grid_rects:
            msg += str(int(rect[0])+1)
        self.sendMsg(msg)

    ## added by bjørn
    def logIn(self):
        if not self.logged_in:
            login_msg = "l%s" % self.player.username
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
                    self.player_number = int(parsed_login[2])
                    self.player.selected_color = self.player_number-1
                    if not self.is_host:
                        self.sendSyncRequest()
                    print("CLIENT: logged into server with username %s as player number %s" % (self.username, self.player_number))
    
    def sendSyncRequest(self):
        print("CLIENT: sending sync request.")
        self.sendMsg("s") # request synced board from server

    def unstableConnection(self, addr):
        print("%s: has unstable connection with server" % self.name)

if __name__ == "__main__":
    pass