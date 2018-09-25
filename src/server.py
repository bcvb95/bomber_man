"""
TODO:
    * make server broadcast moves on a thread
"""
import pygame
import socket
import time
from listener import Listener
from client import Client, Player
from threading import Thread, Lock
from misc import *

IP="127.0.0.1"

S_PORT=8338
C1_PORT=3883
C2_PORT=3838
C3_PORT=7743
C4_PORT=4532

"""
    Message types:

        'l' - login
        'm' - move
        'p' - ping
        'a' - client sending new moves and ack moves
"""

class Server(Listener):
    def __init__(self, ip, port):
        Listener.__init__(self, ip, port)
        
        self.connected_clients = []
        self.recent_moves = []

        self.rec_moves_lock = Lock() 
        self.conn_clients_lock = Lock()

        self.broadcastThread = Thread(target=self._broadcastThreadFun)
        self.broadcastLock = Lock()

    def sendMsg(self, msg, to_ip, to_port):
        """ Send a packet """
        self.sendPacket(msg, to_ip, to_port)

    def receiveMsg(self, data, from_addr):
        """ Overrides the listers receiveMsg, and handles incomming data for the server"""
        msg_type, data = data[0], data[1:]

        if msg_type == 'l': # client login
            self.handleLogin(data, from_addr)

        if msg_type == 'a': # client sending new moves and ack-moves
            self.handleClientMovesAndAcks(data)
    
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
        Calls broadCastRecentMoves every 0.05 second
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
        num_clients = len(self.connected_clients)
        num_recent_moves = len(self.recent_moves)
        
        for i in range(num_clients):
            c_uname, c_ip, c_port = self.connected_clients[i]
            b_msg = "m" 
            # if recent moves to send
            if num_recent_moves > 0:    
                moves_str = recentMovesToStringParser(self.recent_moves)
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
        for move in stringToListParser(new_moves):
            self.recent_moves.append((move, 0))
        splt_ack_moves = stringToListParser(ack_moves)

        # indexes for recent moves to remove
        pop_i  = []
        for i in  range(len(splt_ack_moves)):       # for each ack-move from client
            for j in range(len(self.recent_moves)): # for each recent move from server
                ack = splt_ack_moves[i]
                rec_move = self.recent_moves[j][0]
                if ack == rec_move: # if client acks a recent move
                    self.recent_moves[j] = (rec_move, self.recent_moves[j][1] + 1)
                # if all clients have ackknowledged the move
                if self.recent_moves[j][1] == len(self.connected_clients): 
                    if j not in pop_i:
                        print("acked: %s, with %d number of acks" % (ack, self.recent_moves[j][1]))
                        pop_i.append(j)                    

        # remove completely acked moves
        new_recent = []
        for i in range(len(self.recent_moves)):
            if i not in pop_i:
                new_recent.append(self.recent_moves[i])
        self.recent_moves = new_recent

        self.rec_moves_lock.release()

    def handleLogin(self, data, from_addr):
        """
            Handle login from client
        """
        parsed_login = stringToListParser(data, ' ')
        username = parsed_login[0]
        from_ip = from_addr[0]
        from_port = from_addr[1]

        reply = ""
        # check if user already is logged in
        do_login = True
        self.conn_clients_lock.acquire()
        for user in self.connected_clients:
            already_in = (user[1] == from_ip and user[2] == from_port)
            if already_in:
                do_login = False
                reply = "llogin_failed"
                break
        if do_login:
            new_usr = (username, from_ip, from_port)
            self.connected_clients.append(new_usr)
            num_usr = len(self.connected_clients)
            # send login status followed by username and player-number
            reply = "llogin_success,%s,%d" % (username, num_usr)
        self.conn_clients_lock.release()

        # send login-response to client
        self.sendMsg(reply, from_ip, from_port)


def test_server():
    server = Server(IP,S_PORT)
    client1 = Client(IP, C1_PORT, IP, S_PORT)
    client2 = Client(IP, C2_PORT, IP, S_PORT)
    client3 = Client(IP, C3_PORT, IP, S_PORT)
    client4 = Client(IP, C4_PORT, IP, S_PORT)

    server.listen()
    client1.listen()
    client2.listen()
    client3.listen()
    client4.listen()

    client1.logIn("Client1")
    client2.logIn("Client2")
    client3.logIn("Client3")
    client4.logIn("Client4")    
    time.sleep(1)

    server.startBroadcasting()
    client1.player.make_move("Holla")
    client2.player.make_move("Right")
    client3.player.make_move("left")
    client4.player.make_move("go right now!")

    time.sleep(1)

    server.stopBroadcasting()

    client1.kill()
    client2.kill()
    client3.kill()
    client4.kill()
    server.kill()

if __name__ == "__main__":
    test_server()
