import time
import datetime
from packetmanager import PacketManager

class TestServer(PacketManager):
    def __init__(self, ip, port, multiple_cons=True, name="Server", logfile=None):
        PacketManager.__init__(self, ip, port, multiple_cons, name=name, verbose=True, logfile=logfile)

    def receiveMsg(self, msg, addr):
        print("Server received: %s" % msg)


class TestClient(PacketManager):
    def __init__(self, ip, port, multiple_cons=False, name="Client", logfile=None):
        PacketManager.__init__(self, ip, port, multiple_cons, name=name, verbose=True, logfile=logfile)

    def receiveMsg(self, msg, addr):
        print("Client received: %s" % msg)

def main():
    ip = "127.0.0.1"
    server_port = 6073
    client1_port = 6074

    # Open a file to use as log file
    log_file_handle = open("log.txt", 'w')
    log_file_handle.write("%s\n%sSTART LOG%s\n" % (datetime.datetime.now(), "-"*30, "-"*30))

    # Initialize two packet managers
    server  = TestServer(ip, server_port, logfile=log_file_handle)
    client1 = TestClient(ip, client1_port, logfile=log_file_handle)

    # Start listening
    server.listen()
    client1.listen()

    # Test packets
    server.sendPacket("LOL", ip, client1_port)

    # Kill packet managers
    time.sleep(1)
    server.kill()
    client1.kill()

    # Close the log file
    log_file_handle.close()

if __name__ == "__main__":
    main()