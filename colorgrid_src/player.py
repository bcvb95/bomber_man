import os
from misc import *
from threading import Lock
from client import Client
from server import Server

from colorgrid_consts import *

class Player(object):
    def __init__(self, username, colorgrid,  ip, port, server_ip, server_port, is_server=False):
        self.id = 0
        self.new_moves = []
        self.server = None
        self.is_server = is_server
        log_path = "%s/../log_files_colorgrid/" % os.path.dirname(os.path.abspath(__file__))
        if not os.path.isdir(log_path):
            os.mkdir(log_path)
        logfile_name_client = "%s/output_client_%s:%s.log" % (log_path, ip, port)
        logfile_name_server = "%s/output_server_%s:%s.log" % (log_path, ip, port)
        self.logfile_client = open(logfile_name_client, 'w')
        self.username = username

        self.client = Client(ip, port, server_ip, server_port, self, logfile=self.logfile_client, verbose=True)
        self.client.listen()

        if self.is_server:
            self.logfile_server = open(logfile_name_server, 'w')
            self.server = Server(server_ip, server_port, self, name="Server", logfile=self.logfile_server, verbose=True)
            self.server.listen()
            self.client.is_host = True
            self.client.name = "HostClient"
            self.client.logIn()
            self.awaiting_sync = {}

        self.colorgrid = colorgrid
        self.colorgrid_lock = Lock()
        self.selected_color = 0

    def make_move(self, move):
        self.colorgrid_lock.acquire()
        move = "%s/%d" % (move, self.selected_color)
        self.new_moves.append("m%s:%s:%d" % (self.client.player_number, move, timeInMs()))
        self.colorgrid_lock.release()

    def get_moves(self):
        self.colorgrid_lock.acquire()
        if self.client.verbose: self.client.log("returning moves")
        moves = self.new_moves
        self.new_moves = []
        self.colorgrid_lock.release()
        return moves

    def do_move(self, move):
        self.colorgrid_lock.acquire()
        move_list = stringToListParser(move, ':')
        move_info = move_list[1].split('/')
        rect_i = int(move_info[0]) # what rect to color
        delete = move_info[1] == 'r' # erase color?
        color = int(move_info[2])
        # color the rect!
        if not delete:
            self.colorgrid.colorRect(rect_i, color)
        else:
            self.colorgrid.colorRect(rect_i, -1)
        self.colorgrid_lock.release()

    def clientHandleBoardSync(self, data):
        for i in range(len(self.colorgrid.grid_rects)):
            self.colorgrid.grid_rects[i] = (int(data[i])-1, self.colorgrid.grid_rects[i][1])

    def clientSendSyncResponse(self):
        msg = "u"
        # Add info to msg needed to sync up client
        for rect in self.colorgrid.grid_rects:
            msg += str(int(rect[0])+1)
        self.client.sendMsg(msg)

    def clientSendSyncRequest(self):
        # send sync request to server
        self.client.sendMsg("s")

    def serverHandleSyncRequest(self, data, from_addr):
        self.awaiting_sync[from_addr] = True
        msg = "u"
        self.server.sendMsg(msg, self.client.ip, self.client.port)

    def serverHandleSyncResponse(self, data):
        for addr in self.awaiting_sync:
            if self.awaiting_sync[addr]:
                msg = "s" + data
                self.server.sendMsg(msg, addr[0], addr[1])
                self.awaiting_sync[addr] = False

    def print_players_online(self):
        if self.server != None:
            print(self.server.connected_clients)

    def kill(self):
        self.client.kill()
        self.logfile_client.close()
        if self.server != None:
            self.server.kill()
            self.logfile_server.close()