import socket
import select
import time
from threading import Thread, Lock, Condition
from queue import Queue

TIMEOUT = 0.1

class Listener(object):
    def __init__(self, ip, port):
        # socket
        self.ip = ip
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setblocking(0)
        self.sock.bind((self.ip, self.port))

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
        time.sleep(0.0001)
        while True:
            self.pool_cond.acquire() # lock mutex
            while self.job_queue.empty():
                if self.kill_pool:
                    return # return if pool is being killed
                self.pool_cond.wait() # unlock mutex and wait for cond broadcast
            job = self.job_queue.get(block=False) # get the first job in the queue (don't block)
            if not job: continue # if you didn't get the job anyways
            data, addr = job # unpack job
            self.receiveMsg(data, addr) # call receive with data
            self.job_queue.task_done() # notify the queue that the task is done
            self.pool_cond.release() # unlock mutex

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
            ready = select.select([self.sock], [], [], TIMEOUT) # poll the socket
            if ready[0]: # if packets
                data, addr = self.sock.recvfrom(4096)
                self.pool_cond.acquire()
                self.job_queue.put((data.decode(), addr)) # add packet to job queue
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