from misc import *
from client import Client
from server import Server

class Player(object):
    def __init__(self, ip, port, server_ip, server_port):
        self.id = 0
        self.new_moves = []
        
        self.client = Client(ip, port, server_ip, server_port, self)
        self.server = None

    def make_move(self, move):
        self.new_moves.append("m%s:%s:%d" % (self.id, move, timeInMs()))

    def get_moves(self):
        moves = self.new_moves
        self.new_moves = []
        return moves

    def do_move(self, move):
        move_list = stringToListParser(move, ':')
        print("\n\nMove by: player %s\nMove: %s\nTime: %s" % (move_list[0][1], move_list[1], move_list[2]))