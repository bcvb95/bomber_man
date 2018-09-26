import time
import datetime
import os
from packetmanager import PacketManager

class TestServer(PacketManager):
    def __init__(self, ip, port, name="Server", logfile=None):
        PacketManager.__init__(self, ip, port, name=name, verbose=True, logfile=logfile)

    def receiveMsg(self, msg, addr):
        print("%s received: %s" % (self.name, msg))

    def sendMsg(self, msg, addr):
        self.sendPacket(msg, addr[0], addr[1])


class TestClient(PacketManager):
    def __init__(self, ip, port, server_ip, server_port, name="Client", logfile=None):
        PacketManager.__init__(self, ip, port, name=name, verbose=True, logfile=logfile)
        self.server_ip = server_ip
        self.server_port = server_port

    def receiveMsg(self, msg, addr):
        print("%s received: %s" % (self.name, msg))

    def sendMsg(self, msg):
        self.sendPacket(msg, self.server_ip, self.server_port)

def main():
    ip = "127.0.0.1"
    server_port  = 6073
    client1_port = 6074
    client2_port = 6075
    client3_port = 6076
    client4_port = 6077

    # Open log files
    log_file_handle_s  = open(os.path.dirname(__file__) + "/../test_log/test_server.log", 'w')
    log_file_handle_c1 = open(os.path.dirname(__file__) + "/../test_log/test_client1.log", 'w')
    log_file_handle_c2 = open(os.path.dirname(__file__) + "/../test_log/test_client2.log", 'w')
    log_file_handle_c3 = open(os.path.dirname(__file__) + "/../test_log/test_client3.log", 'w')
    log_file_handle_c4 = open(os.path.dirname(__file__) + "/../test_log/test_client4.log", 'w')

    # Write header with timestamp to log files
    now = datetime.datetime.now()
    log_file_handle_s.write ("%s\n%sSTART LOG%s\n" % (now, "-"*30, "-"*30))
    log_file_handle_c1.write("%s\n%sSTART LOG%s\n" % (now, "-"*30, "-"*30))
    log_file_handle_c2.write("%s\n%sSTART LOG%s\n" % (now, "-"*30, "-"*30))
    log_file_handle_c3.write("%s\n%sSTART LOG%s\n" % (now, "-"*30, "-"*30))
    log_file_handle_c4.write("%s\n%sSTART LOG%s\n" % (now, "-"*30, "-"*30))

    # Initialize packet managers
    server  = TestServer(ip, server_port,  logfile=log_file_handle_s)
    client1 = TestClient(ip, client1_port, ip, server_port, logfile=log_file_handle_c1, name="Client1")
    client2 = TestClient(ip, client2_port, ip, server_port, logfile=log_file_handle_c2, name="Client2")
    client3 = TestClient(ip, client3_port, ip, server_port, logfile=log_file_handle_c3, name="Client3")
    client4 = TestClient(ip, client4_port, ip, server_port, logfile=log_file_handle_c4, name="Client4")
    clients = [client1, client2, client3, client4]
    # Start listening
    server.listen()
    for client in clients:
        client.listen()

    # Test 1: clients sends packet to server
    for client in clients:
        client.sendMsg("hello server i'm %s" % client.name)
    time.sleep(0.1)
    # Test 2: server responds to clients
    server.sendMsg("hello client 1", (ip, client1_port))
    server.sendMsg("hello client 2", (ip, client2_port))
    server.sendMsg("hello client 3", (ip, client3_port))
    server.sendMsg("hello client 4", (ip, client4_port))
    time.sleep(0.1)
    # Test 3: clients send a lot of packets to server
    for i in range(100):
        for client in clients:
            client.sendMsg("this is a StressTest1 packet with number %d from %s" % (i, client.name))
    time.sleep(0.5)
    # Test 4: clients send a lot of packets to server and server responds to each packet
    for i in range(100):
        for client in clients:
            client.sendMsg("this is a StressTest2 packet with number %d from %s" % (i, client.name))
            server.sendMsg("thanks for the StressTest2 packet with number %d %s" % (i, client.name), (client.ip, client.port))
    time.sleep(1)

    # Kill packet managers
    time.sleep(1)
    server.kill()
    client1.kill()
    client2.kill()
    client3.kill()
    client4.kill()

    # Close the log files
    log_file_handle_s.close()
    log_file_handle_c1.close()
    log_file_handle_c2.close()
    log_file_handle_c3.close()
    log_file_handle_c4.close()
    print("-"*50)
    print("The test is over... now.")
    print("Log files placed in ../test_log/")

if __name__ == "__main__":
    main()