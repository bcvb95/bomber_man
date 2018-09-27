from misc import *
from threading import Lock
from client import Client
from server import Server

from colorgrid_consts import *

class Player(object):
    def __init__(self,colorgrid,  ip, port, server_ip, server_port, is_server=False):
        self.id = 0
        self.new_moves = []
        self.server = None
        self.is_server = is_server
        self.logfile = open("./output.log", 'w')

        if self.is_server:
            self.server = Server(server_ip, server_port,name="Server",  logfile=self.logfile, verbose=True)
            self.server.listen()

        self.colorgrid = colorgrid
        self.colorgrid_lock = Lock()
        self.selected_color = 0
        self.client = Client(ip, port, server_ip, server_port, self, logfile=self.logfile, verbose=True)
        self.client.listen()

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
        try:
            color = CLIENT_COLORS[int(move_info[2])]
        except:
            color = BLACK
        # color the rect!
        if not delete:
            self.colorgrid.colorRect(rect_i, color)
        else:
            self.colorgrid.colorRect(rect_i, None)
        self.colorgrid_lock.release()

    def print_players_online(self):
        if self.server != None:
            print(self.server.connected_clients)

    def kill(self):
        self.client.kill()
        if self.server != None:
            self.server.kill()