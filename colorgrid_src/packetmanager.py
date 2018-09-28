import socket
import select
import time
from threading import Thread, Lock, Condition
from queue import Queue

TIMEOUT = 0.1
CHECK_RESEND_FREQ = 0.2
RESEND_TIME = 0.5
RESEND_AMOUNT_TOLERANCE = 5
FRESHNESS_TOLERANCE = 5
WORKER_THREADS = 8
MAX_PACK_SIZE = 4096
STABLE_CON_TOLERANCE = 5

# TODO:
# - FIX BUG: Sequence numbers are some times appended multiple times

# Changelog
# - Interface changes:
#   * Subclasses should now call sendPacket when they want to send packets.
#   * The packet manager can have a custom name for debugging
#   * Verbose mode - Get a lot of output
#   * Log file - If you specify a logfile output is redirected there.
#   * No longer requires 'multiple_cons' arg
# - Backend changes:
#   * Resend packets that are not acknowledged after some time
#   * Don't accept packets that have been seen before by checking sequence numbers

class PacketManager(object):
    def __init__(self, ip, port, name="packetManager", verbose=False, logfile=None):
        # debug
        self.name = name
        self.verbose = verbose
        self.logfile = logfile
        # socket
        self.ip = ip
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # socket is non blocking
        self.sock.setblocking(1)
        self.sock.bind((self.ip, self.port))

        # listener thread
        # the listen thread is stored here
        self.listen_thread = None
        # flag for killing the listener
        self.kill_listen = False
        # mutex to be able to access kill_listen flag
        self.listener_lock = Lock()

        # packet monitoring
        # table of sequence numbers of each connection, used when sending
        self.connection_seqs = {}
        # table of unacknowledged packet lists for each connection, used to resend packets
        self.unacknowledged_packets = {}
        # when was the last resend check?
        self.last_resend_check = time.time()
        # mutex to use for accessing above tables
        self.send_mutex = Lock()
        # table of latest sequence numbers received from client, used when receiving to not handle a packet that has been handled before
        self.client_latest_seqs = {}
        # mutex for checking sequence numbers (and using above table)
        self.checkseq_mutex = Lock()
        # connection stability dict
        self.stable_cons = {}
        self.stable_mutex = Lock()

        # thread pool
        # a Queue object for storing new packets
        self.job_queue = Queue(maxsize=0) # maxsize = 0 = inf
        # flag for killing pool
        self.kill_pool = False
        # mutex and cond object for managing queue
        self.pool_lock = Lock()
        self.pool_cond = Condition(self.pool_lock)
        # initialize worker threads
        for i in range(WORKER_THREADS):
            worker = Thread(target=self._receiveMsg)
            worker.setDaemon(True) # exit when main thread exits
            worker.start()

    def log(self, msg):
        """
        Logs message to logfile if it exists, else it prints to stdout.
        """
        msg = "%s: %s" % (self.name, msg)
        if self.logfile:
            self.logfile.write(msg + "\n")
        else:
            print(msg)

    def kill(self):
        """
        Kill the server.
        """
        if self.verbose: self.log("being killed.")
        self.stop_listen()
        self._kill_pool()

    def listen(self):
        """
        Start listen thread.
        """
        if self.verbose: self.log("starting listen thread")
        self.listen_thread = Thread(target=self._listen_thread)
        self.listen_thread.start()

    def stop_listen(self):
        """
        Stop listen thread.
        """
        if self.verbose: self.log("stopping listen thread")
        self.listener_lock.acquire()
        self.kill_listen = True # This will cause the listen thread to exit
        self.listener_lock.release()
        self.listen_thread.join()

    def sendPacket(self, data, ip, port, ack=False, arg_seq=-1):
        """
        Should always be used to send packets.
        Don't override this function, instead call it in the end of your own send function.
        --------------------------------------------------------------------------------------------
        Sends packets with sequence numbers according to the address it is being sent to.
        Also logs sent packets so they can be resend later if they are not acknowledged in between.
        """
        seq = int(arg_seq)
        addr_key = "%s%s" % (ip, port)
        if seq != -1:
            self.send_mutex.acquire()
        elif not ack:
            self.send_mutex.acquire()
            if addr_key in self.connection_seqs:
                seq = self.connection_seqs[addr_key]
            else:
                seq = 0
            self.connection_seqs[addr_key] = seq + 1

        pack_max_size = MAX_PACK_SIZE-len(str(seq))
        if len(data) > pack_max_size:
            if self.verbose: self.log("ERROR - packet %s to send is %d bytes too big. truncating." % (seq, len(data) - pack_max_size))
            #data = data[:pack_max_size-1]
        data = "%s-%d" % (data, seq)

        if self.verbose: self.log("sending packet: [data='%s', ip='%s', port='%s', seq='%s']" % (data, ip, port, seq))
        self.sock.sendto(data.encode(), (ip, port))
        if not ack:
            # Unacknowledged packet: (data, seq, last_resend, addr, resend_count)
            unack_pack = (data, "%d" % seq, time.time(), (ip, port), 0)
            if addr_key in self.unacknowledged_packets:
                self.unacknowledged_packets[addr_key].append(unack_pack)
            else:
                self.unacknowledged_packets[addr_key] = [unack_pack]
            self.send_mutex.release()

    def receiveMsg(self, data, addr):
        """
        Public method - should be overwritten to handle received packets.
        Called when a new packet has been received and passed checks.
        """
        print("received: %s from %s" % (data, addr))

    def unstableConnection(self, addr):
        """
        Public method - should be overwritten to handle unstable/lost connections.
        Called when a packet has been discarded STABLE_TOLERANCE times.
        """
        print("unstable connection with address: %s:%s" % (addr[0], addr[1]))

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
        """
        Used by worker threads to handle a packet.
        The data is used to call self.receiveMsg (which can be overwritten to use the data for what you like)
        ----------------------------------------------------------------------
        If the packet is an ack packet (prefixed by 'x') the data will not be used for a call to self.receiveMsg.
        Instead it will silently receive the ack and remove the newly acknowledged packet.

        If the packet is not an ack packet the function either accepts or rejects the new packet.
        - If the packet is accepted the data (without sequence number) is used as argument to self.receiveMsg.
        - If the packet is rejected it is put back on the job queue, with a higher freshness value.

        If the packet has a freshness of 1 it is a new packet (only been one the job queue once).
        In this case we send an ack packet back to the sender.

        Packets are accepted if they pass the checks in _checkSeq.
        """
        ori_data = data
        # extract packet type, sequence number and data
        packet_type = data[0]
        try:
            split_data = data.split('-')
            data, seq = split_data[0], split_data[1]
        except IndexError as err:
            if self.verbose: self.log("ERROR - Invalid packet with data %s" % ori_data)
            return
        # handle ack packets
        if packet_type == 'x':
            self._getPacketAck(seq, addr)
            return
        # handle other packets
        if freshness == 0:
            if self.verbose: self.log("received new packet: [data='%s', ip='%s', port='%s', seq='%s']" % (ori_data, addr[0], addr[1], seq))
            self._sendPacketAck(seq, addr[0], addr[1]) # send ack packet for this packet
        else:
            if self.verbose: self.log("handles old packet(f=%d): [data='%s', ip='%s', port='%s', seq='%s']" % (freshness, ori_data, addr[0], addr[1], seq))
        checkSeq_extcode = self._checkSeq(seq, addr, freshness)
        if checkSeq_extcode != 0:
            if self.verbose: self.log("rejected packet(f=%d): [data='%s', ip='%s', port='%s', seq='%s']" % (freshness, ori_data, addr[0], addr[1], seq))
            if checkSeq_extcode == 1:
                self.pool_cond.acquire()
                self.job_queue.put((ori_data, addr, freshness+1)) # put job back to queue
                self.pool_cond.release()
            return
        if self.verbose: self.log("accepted packet(f=%d): [data='%s', ip='%s', port='%s', seq='%s']" % (freshness, ori_data, addr[0], addr[1], seq))
        self.receiveMsg(data, addr) # call receive with data

    def _checkSeq(self, seq, addr, freshness):
        """
        Checks sequence number against stored sequence number from same address.
        Accepts sequence numbers if:
        - They are 0 (stores as new client)
        - They are one larger than stored sequence number (update stored sequence number)
        - If freshness of packet is above FRESHNESS_TOLERANCE and larger than stored (update stored sequence number)
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
        self.checkseq_mutex.acquire()
        if addr_key not in self.client_latest_seqs: # New client
            self.client_latest_seqs[addr_key] = (seq, list(range(0, seq)))
            if self.verbose: self.log("accepted packet with seq %d because it was from a new client." % seq)
            self.checkseq_mutex.release()
            return 0
        if freshness > FRESHNESS_TOLERANCE:
            self.client_latest_seqs[addr_key] = (seq, self.client_latest_seqs[addr_key][1] + list(range(self.client_latest_seqs[addr_key][0], seq)))
            if self.verbose: self.log("accepted packet with seq %d because its freshness was above tolerance." % seq)
            self.checkseq_mutex.release()
            return 0
        if self.client_latest_seqs[addr_key][0] == seq-1:
            self.client_latest_seqs[addr_key] = (seq, self.client_latest_seqs[addr_key][1])
            if self.verbose: self.log("accepted packet with seq %d because it was in correct sequence." % seq)
            self.checkseq_mutex.release()
            return 0

        if len(self.client_latest_seqs[addr_key][1]) > 10:
            self.client_latest_seqs[addr_key] = (self.client_latest_seqs[addr_key][0], self.client_latest_seqs[addr_key][1][-10:])
        missed_seq_list = self.client_latest_seqs[addr_key][1]
        for i in range(len(missed_seq_list)):
            missed_seq = missed_seq_list[i]
            if missed_seq == seq:
                if self.verbose: self.log("accepted packet with seq %d because it was a missing sequence number." % seq)
                del self.client_latest_seqs[addr_key][1][i]
                self.checkseq_mutex.release()
                return 0
        if seq < self.client_latest_seqs[addr_key][0]:
            if self.verbose: self.log("rejected packet with seq %d because it was below stored seq (%d) and not missing." % (seq, self.client_latest_seqs[addr_key][0]))
            self.checkseq_mutex.release()
            return 2
        if self.verbose: self.log("rejected packet with seq %d because it was in wrong sequence. expected seq %d from (%s,%s)" % (seq, self.client_latest_seqs[addr_key][0], addr[0], addr[1]))
        self.checkseq_mutex.release()
        return 1

    def _sendPacketAck(self, seq, ip, port):
        """
        Sends ack for package.
        Ack messages has a 'x' prefix.
        """
        if self.verbose: self.log("sends packet ack for pack with seq %s" % seq)
        self.sendPacket("x-%s" % seq, ip, port, ack=True)

    def _getPacketAck(self, seq, addr):
        """
        Get ack for package.
        Looks through unaccepted packages sent to that address and removes the package that was acknowledged.
        """
        addr_key = "%s%s" % (addr[0], addr[1])
        self.stable_mutex.acquire()
        self.stable_cons[addr_key] = 0
        self.stable_mutex.release()
        self.send_mutex.acquire()
        unack_packets = self.unacknowledged_packets[addr_key]
        for i in range(len(unack_packets)):
            if unack_packets[i][1] == seq:
                if self.verbose: self.log("got packet ack for pack with seq %s" % seq)
                del self.unacknowledged_packets[addr_key][i]
                self.send_mutex.release()
                return
        if self.verbose: self.log("got packet ack for already acknowledged packet with seq %s" % seq)
        self.send_mutex.release()

    def _check_resend(self):
        """
        Checks all unacknowledged packets sent to all peers.
        Resends packet if it has not been acknowledged after RESEND_TIME.
        """
        now = time.time()
        self.last_resend_check = now
        self.send_mutex.acquire()
        for addr_key in self.unacknowledged_packets:
            i = 0
            while i < len(self.unacknowledged_packets[addr_key]):
                # Unacknowledged packet: (data, seq, last_resend, addr)
                packet = self.unacknowledged_packets[addr_key][i]
                if now - packet[2] > RESEND_TIME:
                    if self.verbose: self.log("resending packet with sequence number %s" % packet[1])
                    ip, port = packet[3]
                    self.send_mutex.release()
                    self.sendPacket(packet[0], ip, port, arg_seq=packet[1])
                    self.send_mutex.acquire()
                    if packet[4] >= RESEND_AMOUNT_TOLERANCE:
                        if self.verbose: self.log("discarding unacknowledged packet with seq %s after resending %d times" % (packet[1], RESEND_AMOUNT_TOLERANCE))
                        del self.unacknowledged_packets[addr_key][i]
                        self.stable_mutex.acquire()
                        if addr_key not in self.stable_cons:
                            self.stable_cons[addr_key] = 0
                        self.stable_cons[addr_key] += 1
                        if self.stable_cons[addr_key] >= STABLE_CON_TOLERANCE:
                            self._unstableConnection((ip, port))
                            self.stable_mutex.release()
                            break
                        self.stable_mutex.release()
                        continue
                    else:
                        self.unacknowledged_packets[addr_key][i] = (packet[0], packet[1], now, packet[3], packet[4]+1)
                i += 1
        self.send_mutex.release()

    def _unstableConnection(self, addr):
        if self.verbose: self.log("has unstable connection with address: %s:%s" % (addr[0], addr[1]))
        addr_key = "%s%s" % (addr[0], addr[1])
        self.checkseq_mutex.acquire()
        del self.client_latest_seqs[addr_key]
        self.checkseq_mutex.release()
        # already have send mutex
        self.unacknowledged_packets[addr_key] = []
        del self.connection_seqs[addr_key]
        # already have stable mutex
        del self.stable_cons[addr_key]
        self.unstableConnection(addr)


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
            self.listener_lock.release()
            now = time.time()
            if now - self.last_resend_check > CHECK_RESEND_FREQ:
                self._check_resend()
            ready = select.select([self.sock], [], [], TIMEOUT) # poll the socket
            if ready[0]: # if packets
                data, addr = self.sock.recvfrom(MAX_PACK_SIZE)
                self.pool_cond.acquire()
                self.job_queue.put((data.decode(), addr, 0)) # add packet to job queue
                self.pool_cond.notify_all() # notify workers
                self.pool_cond.release()

    def _kill_pool(self):
        """
        Private method - should not be called from outside the class.
        Kills the job queue.
        """
        if self.verbose: self.log("killing worker pool.")
        self.pool_cond.acquire()
        self.kill_pool = True
        self.job_queue.join()
        self.pool_cond.notify_all()
        self.pool_cond.release()