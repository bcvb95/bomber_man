import pygame
import socket
import time
import misc

from packetmanager import PacketManager

STALLED_TOLERANCE = 10

class Client(PacketManager):
    def __init__(self, ip, port, serverIP, serverPort, player, name="Client", logfile=None, verbose=False):
        PacketManager.__init__(self, ip, port, name, logfile=logfile, verbose=verbose)
        self.serverIP = serverIP
        self.serverPort = serverPort
        self.latest_move = 0
        self.player = player

        self.server_seq = -1
        self.stalled_packets = []

        self.logged_in = False
        self.username = ""
        self.player_number = None
        self.should_sync = False

        self.is_host = False

    def sendMsg(self, msg):
        self.sendPacket(msg, self.serverIP, self.serverPort)

    def receiveMsg(self, data, addr, forced=False):
        orig_data = data
        msg_type, data = data[0], data[1:]
        data_lst = data.split('>')
        data, seq = data_lst[0].strip(), int(data_lst[1].strip())
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
            self.player.clientHandleBoardSync(data)
        elif msg_type == 'u':
            self.player.clientSendSyncResponse()
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
        new_moves = misc.listToStringParser(self.player.get_moves())
        ack_moves = misc.listToStringParser(ack_moves)
        self.sendMsg("a" + ack_moves + ";" + new_moves)

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
                parsed_login = misc.stringToListParser(data, seperator=',')
                login_resp = parsed_login[0]
                # get login response
                if login_resp == "login_failed":
                    self.logged_in = False
                elif login_resp == "login_success":
                    self.logged_in = True
                    self.username = parsed_login[1]
                    self.player_number = int(parsed_login[2])
                    self.player.selected_color = self.player_number-1
                    if not self.is_host and self.should_sync:
                        self.player.clientSendSyncRequest()
                    print("CLIENT: logged into server with username %s as player number %s" % (self.username, self.player_number))


    def unstableConnection(self, addr):
        print("%s: has unstable connection with server" % self.name)

if __name__ == "__main__":
    pass