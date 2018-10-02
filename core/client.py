import pygame
import socket
import time
import misc
from threading import Lock, Condition
from packetmanager import PacketManager

class Client(PacketManager):
    def __init__(self, ip, port, serverIP, serverPort, player, name="Client", logfile=None, verbose=False):
        PacketManager.__init__(self, ip, port, name, logfile=logfile, verbose=verbose)
        self.serverIP = serverIP
        self.serverPort = serverPort
        self.latest_move = 0
        self.player = player
        self.game_manager = None

        self.newest_move_seq = -1

        self.logged_in = False
        self.login_lock = Lock()
        self.login_cond = Condition(self.login_lock)

        self.username = ""
        self.player_number = None
        self.should_sync = False

        self.is_host = False
        self.init_game_lock = Lock()
        self.init_game = False
        self.init_num_players = 0

    def sendMsg(self, msg):
        self.sendPacket(msg, self.serverIP, self.serverPort)

    def receiveMsg(self, data, addr):
        orig_data = data
        msg_type, data = data[0], data[1:]
        if msg_type == 'l':
            self.handleLoginResponse(data, addr)
        elif msg_type == 'i':
            self.handleInitGame(data)
        elif msg_type == 's':
            self.player.clientHandleBoardSync(data)
        elif msg_type == 'u':
            self.player.clientSendSyncResponse()
        elif msg_type == 'm': # new moves
            self.handleNewMovesPacket(data)

    def handleNewMovesPacket(self, data):
        ack_moves = []
        if len(data) > 0:
            moves = data.split(',')
            for i in range(len(moves)):
                if len(moves[i][0]) == 0: continue
                move_split = moves[i].split('>')
                move, move_seq = move_split[0], int(move_split[1])
                if move_seq > self.newest_move_seq:
                    self.newest_move_seq = move_seq
                    ack_moves.append(moves[i])
                    self.game_manager.execute_move(moves[i])
        new_moves = misc.listToStringParser(self.player.get_moves())
        ack_moves = misc.listToStringParser(ack_moves)
        self.sendMsg("a" + ack_moves + ";" + new_moves)

    ## added by bjørn
    def logIn(self):
        self.login_cond.acquire()
        while True:
            if self.logged_in:
                self.login_cond.release()
                break
            login_msg = "l%s" % self.player.username
            self.sendMsg(login_msg)
            self.login_cond.wait()

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
                    self.login_cond.acquire()
                    self.logged_in = True
                    self.login_cond.notifyAll()
                    self.login_cond.release()

                    self.username = parsed_login[1]
                    self.player_number = int(parsed_login[2])
                    self.player.selected_color = self.player_number-1
                    if not self.is_host and self.should_sync:
                        self.player.clientSendSyncRequest()
                    print("CLIENT: logged into server with username %s as player number %s" % (self.username, self.player_number))

    def handleInitGame(self, data):
        self.init_game_lock.acquire()
        self.init_game = True
        self.init_num_players = int(data[-1])
        self.init_game_lock.release()

    def doInitGame(self):
        res = False
        self.init_game_lock.acquire()
        res = self.init_game
        self.init_game_lock.release()
        return res

    def unstableConnection(self, addr):
        print("%s: has unstable connection with server" % self.name)

if __name__ == "__main__":
    pass