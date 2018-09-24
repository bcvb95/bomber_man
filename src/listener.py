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
        self.stop_listen()
        self.kill_pool = True
        self.job_queue.join()

    def _receiveMsg(self):
        time.sleep(0.0001)
        while True:
            if self.kill_pool:
                return
            self.pool_cond.acquire()
            while self.job_queue.empty():
                self.pool_cond.wait()
            data, addr = self.job_queue.get(block=False)
            self.receiveMsg(data, addr)
            self.job_queue.task_done()
            self.pool_cond.release()

    def receiveMsg(self, data, addr):
        print("received: %s from %s" % (data, addr))

    def listen(self):
        self.listen_thread = Thread(target=self._listen_thread)
        self.listen_thread.start()

    def stop_listen(self):
        self.listener_lock.acquire()
        self.kill_listen = True
        self.listener_lock.release()
        self.listen_thread.join()

    def _listen_thread(self):
        while 1:
            time.sleep(0.0001) # without this the lock will be reacquired almost every time
            self.listener_lock.acquire()
            if self.kill_listen:
                return
            ready = select.select([self.sock], [], [], TIMEOUT)
            if ready[0]:
                data, addr = self.sock.recvfrom(4096)
                self.pool_cond.acquire()
                self.job_queue.put((data.decode(), addr))
                self.pool_cond.notify_all()
                self.pool_cond.release()
            self.listener_lock.release()
