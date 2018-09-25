import socket
import select
import time
from threading import Thread, Lock, Condition
from queue import Queue

TIMEOUT = 0.1
CHECK_RESEND_FREQ = 0.2
RESEND_TIME = 0.5
FRESHNESS_TOLERANCE = 5

# TODO:
# - Verbose mode
# - Log file
# - Tests for this class

# Changelog
# - Interface changes:
#   * Subclasses should now call sendPacket when they want to send packets.
#   * The listener can have a custom name for debugging
#   * NOT DONE: Verbose mode
# - Backend changes:
#   * Resend packets that are not acknowledged after some time
#   * Don't accept packets that have been seen before by checking sequence numbers

class Listener(object):
    def __init__(self, ip, port, name="listener", verbose=False, logfile=None):
        # debug
        self.name = name
        self.verbose = verbose
        self.logfile = logfile
        # socket
        self.ip = ip
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setblocking(0)
        self.sock.bind((self.ip, self.port))

        # packet resending
        self.seq = 0
        self.unacknowledged_packets = []
        self.last_resend_check = time.time()
        self.client_seqs = {}

        # listener thread
        self.listen_thread = None
        self.listener_lock = Lock()
        self.kill_listen = False

        # thread pool
        self.job_queue = Queue(maxsize=0) # maxsize = 0 = inf
        self.pool_lock = Lock()
        self.pool_cond = Condition(self.pool_lock)
        self.numthreads = 8
        self.kill_pool = False
        for i in range(self.numthreads):
            worker = Thread(target=self._receiveMsg)
            worker.setDaemon(True) # exit when main thread exits
            worker.start()

    def kill(self):
        """
        Kill the server.
        """
        if self.verbose: self.log("%s: being killed." % self.name)
        self.stop_listen()
        self._kill_pool()

    def log(self, msg):
        if self.logfile:
            self.logfile.write(msg+'\n')
        else:
            print(msg)

    def listen(self):
        """
        Start listen thread.
        """
        if self.verbose: self.log("%s starting listen thread" % self.name)
        self.listen_thread = Thread(target=self._listen_thread)
        self.listen_thread.start()

    def stop_listen(self):
        """
        Stop listen thread.
        """
        if self.verbose: self.log("%s stopping listen thread" % self.name)
        self.listener_lock.acquire()
        self.kill_listen = True # This will cause the listen thread to exit
        self.listener_lock.release()
        self.listen_thread.join()

    def sendPacket(self, data, ip, port, ack=False, arg_seq=-1):
        seq = arg_seq
        if seq != -1:
            data = "%s-%s" % (data, seq)
        elif not ack:
            data = "%s-%d" % (data, self.seq)
            self.unacknowledged_packets.append((data, "%d" % self.seq, time.time(), (ip, port)))
            self.seq += 1
            seq = self.seq
        if self.verbose: self.log("%s sending packet: [data='%s', ip='%s', port='%s', seq='%s']" % (self.name, data, ip, port, seq))
        self.sock.sendto(data.encode(), (ip, port))

    def receiveMsg(self, data, addr):
        """
        Public method - should be overwritten.
        """
        print("received: %s from %s" % (data, addr))

    def _receiveMsg(self):
        """
        Private method - should not be overwritten or called from outside the class.
        This method is run by the worker threads.
        """
        while True:
            self.pool_cond.acquire() # lock mutex
            while self.job_queue.empty():
                if self.kill_pool:
                    return # return if pool is being killed
                self.pool_cond.wait() # unlock mutex and wait for cond broadcast
            job = self.job_queue.get(block=False) # get the first job in the queue (don't block)
            self.job_queue.task_done() # notify the queue that the task is done
            self.pool_cond.release() # unlock mutex
            if not job: continue # if you didn't get the job anyways
            data, addr, job_freshness = job # unpack job
            self._handlePacket(data, addr, job_freshness)

    def _handlePacket(self, data, addr, freshness):
        ori_data = data
        # extract packet type, sequence number and data
        packet_type = data[0]
        split_data = data.split('-')
        data, seq = split_data[0], split_data[1]
        # handle ack packets
        if packet_type == 'x':
            self._getPacketAck(seq)
            return
        # handle other packets
        if freshness == 0:
            if self.verbose: self.log("%s received new packet: [data='%s', ip='%s', port='%s', seq='%s']" % (self.name, ori_data, addr[0], addr[1], seq))
            self._sendPacketAck(seq, addr[0], addr[1]) # send ack packet for this packet
        else:
            if self.verbose: self.log("%s handles old packet(f=%d): [data='%s', ip='%s', port='%s', seq='%s']" % (self.name, freshness, ori_data, addr[0], addr[1], seq))
        if self._checkSeq(seq, addr, freshness) == 1:
            if self.verbose: self.log("%s rejected packet(f=%d): [data='%s', ip='%s', port='%s', seq='%s']" % (self.name, freshness, ori_data, addr[0], addr[1], seq))
            self.pool_cond.acquire()
            self.job_queue.put((ori_data, addr, freshness+1)) # put job back to queue
            self.pool_cond.release()
            return
        if self.verbose: self.log("%s accepted packet(f=%d): [data='%s', ip='%s', port='%s', seq='%s']" % (self.name, freshness, ori_data, addr[0], addr[1], seq))
        self.receiveMsg(data, addr) # call receive with data

    def _checkSeq(self, seq, addr, freshness):
        """
        Checks sequence number against stored sequence number from same address.
        Accepts sequence numbers if:
        - They are 0 (stores as new client)
        - They are one larger than stored sequence number (update stored sequence number)
        - If freshness of packet is above FRESHNESS_TOLERANCE (update stored sequence number)
        - They are smaller than stored sequence number and in missed sequence numbers (don't update stored sequence number)
        Does not accept sequence numbers if:
        - They are smaller than stored sequence number and not in missed sequence numbers

        The client_seqs dictionary is structured as following:
        - Keys are the ipadress and port concatenated, like '127.0.0.18080'
        - Values are tuples where
          * first element is stored sequence number
          * second element is list of missed sequence numbers

        Exit codes:
        - 0: Sequence accepted
        - 1: Sequence not accepted
        """
        addr_key = "%s%s" % (addr[0], addr[1])
        seq = int(seq)
        if addr_key not in self.client_seqs: # New client
            self.client_seqs[addr_key] = (seq, list(range(0, seq)))
            if self.verbose: self.log("%s accepted packet with seq %d because it was from a new client." % (self.name, seq))
            return 0
        if freshness > FRESHNESS_TOLERANCE:
            self.client_seqs[addr_key] = (seq, self.client_seqs[addr_key][1] + list(range(self.client_seqs[addr_key][0], seq)))
            if self.verbose: self.log("%s accepted packet with seq %d because its freshness was above tolerance." % (self.name, seq))
            return 0
        if self.client_seqs[addr_key][0] == seq-1:
            self.client_seqs[addr_key] = (seq, self.client_seqs[addr_key][1])
            if self.verbose: self.log("%s accepted packet with seq %d because it was in correct sequence." % (self.name, seq))
            return 0
        if addr_key in self.client_seqs:
            missed_seq_list = self.client_seqs[addr_key][1]
            if len(missed_seq_list) > 10:
                self.client_seqs[addr_key][1] = missed_seq_list[-10:]
            for i in range(len(missed_seq_list)):
                missed_seq = missed_seq_list[i]
                if missed_seq == seq:
                    if self.verbose: self.log("%s accepted packet with seq %d because it was a missing sequence number." % (self.name, seq))
                    del self.client_seqs[addr_key][1][i]
                    return 0
        return 1

    def _sendPacketAck(self, seq, ip, port):
        if self.verbose: self.log("%s sends packet ack for pack with seq %s" % (self.name, seq))
        self.sendPacket("x-%s" % seq, ip, port, ack=True)

    def _getPacketAck(self, seq):
        for i in range(len(self.unacknowledged_packets)):
            if self.unacknowledged_packets[i][1] == seq:
                if self.verbose: self.log("%s got packet ack for pack with seq %s" % (self.name, seq))
                del self.unacknowledged_packets[i]
                return
        if self.verbose: self.log("%s got packet ack for already acknowledged packet with seq %s" % (self.name, seq))

    def _check_resend(self):
        now = time.time()
        self.last_resend_check = now
        for i in range(len(self.unacknowledged_packets)):
            packet = self.unacknowledged_packets[i]
            if now - packet[2] > RESEND_TIME:
                if self.verbose: print("%s resending packet with sequence number %s" % (self.name, packet[1]))
                ip, port = packet[3]
                self.sendPacket(packet[0], ip, port, arg_seq=packet[1])
                self.unacknowledged_packets[i] = (packet[0], packet[1], now, packet[3])

    def _listen_thread(self):
        """
        Private method - should not be called from outside the class.
        The listen thread calls this function.
        Listens for new packets and adds them to job queue.
        """
        while 1:
            time.sleep(0.0001) # without this the lock will be reacquired almost every time (leaving no time for killing the thread)
            self.listener_lock.acquire()
            if self.kill_listen:
                return # return if listener is being killed
            now = time.time()
            if now - self.last_resend_check > CHECK_RESEND_FREQ:
                self._check_resend()
            ready = select.select([self.sock], [], [], TIMEOUT) # poll the socket
            if ready[0]: # if packets
                data, addr = self.sock.recvfrom(4096)
                self.pool_cond.acquire()
                self.job_queue.put((data.decode(), addr, 0)) # add packet to job queue
                self.pool_cond.notify_all() # notify workers
                self.pool_cond.release()
            self.listener_lock.release()

    def _kill_pool(self):
        """
        Private method - should not be called from outside the class.
        Kills the job queue
        """
        if self.verbose: self.log("%s killing worker pool." % self.name)
        self.pool_cond.acquire()
        self.kill_pool = True
        self.job_queue.join()
        self.pool_cond.notify_all()
        self.pool_cond.release()