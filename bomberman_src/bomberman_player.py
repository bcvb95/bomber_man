import misc
from threading import Lock
from base_player import BasePlayer

class BMPlayer(BasePlayer):
    def __init__(self, username,  ip, port, server_ip, server_port, is_server=False):
        BasePlayer.__init__(self, username, ip, port, server_ip, server_port, is_server) 

    # ----- Required method for BasePlayer ------ #
    def make_move(self, move):
        move = "%s" % (move)
        self.new_moves.append("m%s:%s:%d" % (self.client.player_number, move, misc.timeInMs()))
    
    # ----- Required method for BasePlayer ------ #
    def get_moves(self):
        moves = self.new_moves
        self.new_moves = []
        return moves

    # ----- Required method for BasePlayer ------ #
    def do_move(self, move):
        move_list = misc.stringToListParser(move, ':')
        print("do_moves: ", move_list)