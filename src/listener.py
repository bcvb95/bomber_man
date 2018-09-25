import socket
import select
import time
from threading import Thread, Lock, Condition
from queue import Queue

TIMEOUT = 0.1
CHECK_RESEND_FREQ = 0.2
RESEND_TIME = 0.5

# TODO:
# - Add sequence number to normal packets
# - Introduce ACK packets
# - Resend packets that are not acknowledged
# - Check if sequence number has been seen before when receiving packet
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
#   * NOT DONE: Don't accept packets that have been seen before

class Listener(object):
    def __init__(self, ip, port, name="listener", verbose=False):
        # debug
        self.name = name
        self.verbose = verbose
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
        self.stop_listen()
        self._kill_pool()

    def listen(self):
        """
        Start listen thread.
        """
        self.listen_thread = Thread(target=self._listen_thread)
        self.listen_thread.start()

    def stop_listen(self):
        """
        Stop listen thread.
        """
        self.listener_lock.acquire()
        self.kill_listen = True # This will cause the listen thread to exit
        self.listener_lock.release()
        self.listen_thread.join()

    def sendPacket(self, data, ip, port, ack=False, arg_seq=-1):
        if arg_seq != -1:
            data = "%s-%s" % (data, arg_seq)
        elif not ack:
            data = "%s-%d" % (data, self.seq)
            self.unacknowledged_packets.append((data, "%d" % self.seq, time.time(), (ip, port)))
            self.seq += 1
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
            self._sendPacketAck(seq, addr[0], addr[1]) # send ack packet for this packet
        self.receiveMsg(data, addr) # call receive with data

    def _sendPacketAck(self, seq, ip, port):
        self.sendPacket("x-%s" % seq, ip, port, ack=True)

    def _getPacketAck(self, seq):
        for i in range(len(self.unacknowledged_packets)):
            if self.unacknowledged_packets[i][1] == seq:
                del self.unacknowledged_packets[i]
                return

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
        self.pool_cond.acquire()
        self.kill_pool = True
        self.job_queue.join()
        self.pool_cond.notify_all()
        self.pool_cond.release()