"""
TODO:
    *

"""
import pygame
import socket
import time
import misc
from packetmanager import PacketManager
from client import Client
from threading import Thread, Lock

"""
    Message types:

        'l' - client login
        'm' - client move
        'a' - client sending new moves and ack moves
        's' - client requests sync
        'u' - host client replying with sync
"""

MAX_CLIENTS = 4

class Server(PacketManager):
    def __init__(self, ip, port, player, name="Server", logfile=None, verbose=False):
        PacketManager.__init__(self, ip, port,name=name, logfile=logfile, verbose=verbose)
        self.player = player

        self.connected_clients = []
        self.num_clients = 0
        self.recent_moves = []

        self.rec_moves_lock = Lock()
        self.conn_clients_lock = Lock()

        self.broadcastThread = Thread(target=self._broadcastThreadFun)
        self.broadcastLock = Lock()

        self.con_seqs = {}
        self.con_seqs_lock = Lock()

    def sendMsg(self, msg, to_ip, to_port):
        """ Send a packet """
        addr_key = "%s%s" % (to_ip, to_port)
        self.con_seqs_lock.acquire()
        if addr_key in self.con_seqs:
            self.con_seqs[addr_key] += 1
            seq = self.con_seqs[addr_key]
        else:
            seq = 0
            self.con_seqs[addr_key] = seq
        self.con_seqs_lock.release()
        msg = "%s>%d" % (msg, seq)
        self.sendPacket(msg, to_ip, to_port)

    def receiveMsg(self, data, from_addr):
        """ Overrides the PacketManager receiveMsg, and handles incomming data for the server"""
        msg_type, data = data[0], data[1:]

        if msg_type == 'l': # client login
            self.handleLogin(data, from_addr)
        elif msg_type == 'a': # client sending new moves and ack-moves
            self.handleClientMovesAndAcks(data)
        elif msg_type == 's':
            self.player.serverHandleSyncRequest(data, from_addr)
        elif msg_type == 'u':
            self.player.serverHandleSyncResponse(data)

    def unstableConnection(self, addr):
        """ Overrides the PacketManager unstableConnection.
            Handles an unstable connection as a lost connection """
        addr_key = "%s%s" % (addr[0], addr[1])
        self.con_seqs_lock.acquire()
        del self.con_seqs[addr_key]
        self.con_seqs_lock.release()
        if self.verbose: self.log("unstable client at %s:%s" % (addr[0], addr[1]))
        self.removeClient(addr)

    def removeClient(self, target_addr):
        target_ip, target_port = target_addr
        for i in range(len(self.connected_clients)):
            tmp_client = self.connected_clients[i]
            if not tmp_client: continue
            if target_ip == tmp_client[1] and target_port == tmp_client[2]:
                self.connected_clients[i] = None
                self.num_clients -= 1
                if self.verbose: self.log("removing client %s" % tmp_client[0])
                return

    def startBroadcasting(self):
        """ Starts the broadcasting thread """
        self.broadcastLock.acquire()
        self.do_broadcast = True
        self.broadcastThread.start()
        self.broadcastLock.release()

    def stopBroadcasting(self):
        """ Stops the broadcasting thread """
        self.broadcastLock.acquire()
        self.do_broadcast = False
        self.broadcastLock.release()
        self.broadcastThread.join()

    def _broadcastThreadFun(self):
        """
        Calls broadcast function as much as possible
        """
        self.broadcastLock.acquire()
        doBC = self.do_broadcast
        self.broadcastLock.release()

        while doBC:
            self.broadcastRecentMoves()
            # sleep before next broadcast
            time.sleep(0.05)
            self.broadcastLock.acquire()
            doBC = self.do_broadcast
            self.broadcastLock.release()

    def broadcastRecentMoves(self):
        """
            Broadcasts recent moves to all logged in clients
        """
        self.conn_clients_lock.acquire()
        self.rec_moves_lock.acquire()
        num_recent_moves = len(self.recent_moves)

        for i in range(len(self.connected_clients)):
            if not self.connected_clients[i]: continue
            c_uname, c_ip, c_port = self.connected_clients[i]
            b_msg = "m"
            # if recent moves to send
            if num_recent_moves > 0:
                moves_str = misc.recentMovesToStringParser(self.recent_moves)
                b_msg += moves_str
            else:
                pass # do nothing

            self.sendMsg(b_msg, c_ip, c_port)
        self.conn_clients_lock.release()
        self.rec_moves_lock.release()


    def handleClientMovesAndAcks(self, data):
        """
            Handle clients sending new- and acknowlegded moves.
        """

        splt = data.split(';')
        new_moves = splt[1]
        ack_moves = splt[0]

        # add new moves
        self.rec_moves_lock.acquire()
        for move in misc.stringToListParser(new_moves):
            move_new_time = misc.stringToListParser(move, ':')
            move_new_time[2] = str(misc.timeInMs())
            self.recent_moves.append((misc.listToStringParser(move_new_time, ':'), 0))
        splt_ack_moves = misc.stringToListParser(ack_moves)

        # indexes for recent moves to remove
        pop_i  = []
        for i in  range(len(splt_ack_moves)):       # for each ack-move from client
            for j in range(len(self.recent_moves)): # for each recent move from server
                ack = splt_ack_moves[i]
                rec_move = self.recent_moves[j][0]
                if ack == rec_move: # if client acks a recent move
                    self.recent_moves[j] = (rec_move, self.recent_moves[j][1] + 1)
                # if all clients have ackknowledged the move
                if self.recent_moves[j][1] >= self.num_clients:
                    if j not in pop_i:
                        pop_i.append(j)

        # remove completely acked moves
        new_recent = []
        for i in range(len(self.recent_moves)):
            if i not in pop_i:
                new_recent.append(self.recent_moves[i])

        self.recent_moves = new_recent

        self.rec_moves_lock.release()

    def handleSyncRequest(self, data, from_addr):
        print("SERVER: received sync request!")

    def handleSyncResponse(self, data):
        print("SERVER: handling sync response!")

    def handleLogin(self, data, from_addr):
        """
            Handle login from client
        """
        parsed_login = misc.stringToListParser(data, ' ')
        username = parsed_login[0]
        from_ip = from_addr[0]
        from_port = from_addr[1]

        reply = ""
        # check if user already is logged in
        do_login = True
        self.conn_clients_lock.acquire()
        for user in self.connected_clients:
            if not user: continue
            already_in = (user[1] == from_ip and user[2] == from_port)
            if already_in:
                do_login = False
                reply = "llogin_failed"
                break
        if do_login:
            new_usr = (username, from_ip, from_port)
            new_id = -1
            for i in range(len(self.connected_clients)):
                if self.connected_clients[i]: continue # continue if not free spot
                self.connected_clients[i] = new_usr
                new_id = i+1
                break
            if new_id == -1 and len(self.connected_clients) < MAX_CLIENTS:
                self.connected_clients.append(new_usr)
                new_id = len(self.connected_clients)
            if new_id != -1:
                # send login status followed by username and player-number
                self.num_clients += 1
                reply = "llogin_success,%s,%d" % (username, new_id)
                if self.verbose: self.log("client '%s' logged in succesfully." % username)
            else:
                reply = "llogin_failed"
                if self.verbose: self.log("client '%s' was refused to log in." % username)
        self.conn_clients_lock.release()

        # send login-response to client
        self.sendMsg(reply, from_ip, from_port)

    def sendInitGame(self):
        msg = 'i/' + str(len(self.connected_clients))
        for i in range(len(self.connected_clients)):
            usr_name, client_ip, client_port = self.connected_clients[i]
            self.sendMsg(msg, client_ip, client_port)

if __name__ == "__main__":
    pass