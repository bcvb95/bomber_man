import misc
from threading import Lock
from base_player import BasePlayer

class BMPlayer(BasePlayer):
    def __init__(self, username,  ip, port, server_ip, server_port, is_server=False):
        BasePlayer.__init__(self, username, ip, port, server_ip, server_port, is_server)
        self.init_num_players = 0
        self.layout = 0

    # ----- Required method for BasePlayer ------ #
    def make_move(self, move):
        move = "%s" % (move)
        self.new_moves.append("m%s:%s:%d" % (self.client.player_number, move, misc.timeInMs()))

    # ----- Required method for BasePlayer ------ #
    def get_moves(self):
        moves = self.new_moves
        self.new_moves = []
        return moves

    def init_game(self, init_msg):
        msg_split = init_msg.split('/')
        self.init_num_players = int(msg_split[1])
        if len(msg_split) == 3 and len(msg_split[2]) > 0:
            self.layout = int(msg_split[2])