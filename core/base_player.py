import os
from misc import *
from threading import Lock
from client import Client
from server import Server

class BasePlayer(object):
    def __init__(self, username, ip, port, server_ip, server_port, is_server=False):
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

        # Every player is/has a client
        self.client = Client(ip, port, server_ip, server_port, self, logfile=self.logfile_client, verbose=True)
        self.client.listen()

        if self.is_server:
            # If the player is also a server, start the server and log in as a client
            self.logfile_server = open(logfile_name_server, 'w')
            self.server = Server(server_ip, server_port, self, name="Server", logfile=self.logfile_server, verbose=True)
            self.server.listen()
            self.client.is_host = True
            self.client.name = "HostClient"
            self.client.logIn()
            self.awaiting_sync = {}

    def make_move(self, move):
        """Adds a new move to the players move-list"""
        move = "%s" % move
        self.new_moves.append("m%s:%s:%d" % (self.client.player_number, move, timeInMs()))

    def get_moves(self):
        """ Returns a list of the players move-list."""
        if self.client.verbose: self.client.log("returning moves")
        moves = self.new_moves
        self.new_moves = []
        return moves

    def do_move(self, move):
        """ Is called when a move is to be executed by the player"""
        print("Do move: %s" % move)