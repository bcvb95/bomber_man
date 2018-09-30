import misc
from threading import Lock

from base_player import BasePlayer
from colorgrid_consts import *

class CGPlayer(BasePlayer):
    def __init__(self, username, colorgrid,  ip, port, server_ip, server_port, is_server=False):
        BasePlayer.__init__(self, username, ip, port, server_ip, server_port, is_server) 

        self.colorgrid = colorgrid
        self.colorgrid_lock = Lock()
        self.selected_color = 0

    # ----- Required method for BasePlayer ------ #
    def make_move(self, move):
        self.colorgrid_lock.acquire()
        move = "%s/%d" % (move, self.selected_color)
        self.new_moves.append("m%s:%s:%d" % (self.client.player_number, move, misc.timeInMs()))
        self.colorgrid_lock.release()

    # ----- Required method for BasePlayer ------ #
    def get_moves(self):
        self.colorgrid_lock.acquire()
        if self.client.verbose: self.client.log("returning moves")
        moves = self.new_moves
        self.new_moves = []
        self.colorgrid_lock.release()
        return moves

    # ----- Required method for BasePlayer ------ #
    def do_move(self, move):
        self.colorgrid_lock.acquire()
        move_list = misc.stringToListParser(move, ':')
        move_info = move_list[1].split('/')
        rect_i = int(move_info[0]) # what rect to color
        delete = move_info[1] == 'r' # erase color?
        color = int(move_info[2])
        # color the rect!
        if not delete:
            self.colorgrid.colorRect(rect_i, color)
        self.colorgrid_lock.release()


    # ----- Rest of methods is game specific methods------ #

    def clientHandleBoardSync(self, data):
        for i in range(len(self.colorgrid.grid_rects)):
            self.colorgrid.grid_rects[i] = (int(data[i])-1, self.colorgrid.grid_rects[i][1])
        msg = "u"
        # Add info to msg needed to sync up client
        for rect in self.colorgrid.grid_rects:
            msg += str(int(rect[0])+1)
        self.client.sendMsg(msg)

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