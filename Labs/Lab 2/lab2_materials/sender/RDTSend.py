#!/usr/bin/python3

from socket import *
import threading
import struct
import sys
import random


# simulate packet loss
def lostPacket(seq_num, bound=0.1):
    prob = random.random()
    if prob < bound:
        print("Packet sent from Sender with seq_num %d lost" % seq_num)
        return True
    else:
        return False


class RDTSend:

    def __init__(
        self,
        sender_socket,
        pkt_data,
        RECV_IP,
        RECV_PORT,
        packer,
        unpacker,
        bound,
        window_size,
    ) -> None:
        self.sender_socket = sender_socket
        self.pkt_data = pkt_data
        self.RECV_IP = RECV_IP
        self.RECV_PORT = RECV_PORT
        self.packer = packer
        self.unpacker = unpacker
        self.bound = bound
        self.window_size = window_size

        self.base = 1
        self.next_seq_num = 1
        self.timer = None
        self.stop = False

    def funcTimeout(self):
        self.timer = threading.Timer(2, self.funcTimeout)
        self.timer.start()

        # TODO: retransmit unacked packets from base to next_seq_num-1
        for i in range(self.base, self.next_seq_num):
            pkt = self.pkt_data[i - 1]
            try:
                # Pack data into binary
                packed_data = self.packer.pack(
                    i, bytes(pkt, encoding="utf-8")
                )
            except struct.error as emsg:
                print("Pack data error: ", emsg)
                sys.exit(1)

            if lostPacket(i, self.bound) is False:
                try:
                    self.sender_socket.sendto(
                        packed_data, (self.RECV_IP, self.RECV_PORT)
                    )
                    print("Packet (seq num: %d) retransmitted" % i)
                except error as emsg:
                    print("Socket send error: ", emsg)
                    sys.exit(1)

    def send_data(self):
        recv_task = threading.Thread(target=self.recvAck, args=(2,))
        recv_task.start()
        self.sendPacket()
        recv_task.join()
        self.sender_socket.close()

    # set timer to receive correct ACK
    def recvAck(self, t):
        while not self.stop:
            try:
                data_recv, _ = self.sender_socket.recvfrom(1024)
            except timeout:
                continue

            try:
                unpacked_data = self.unpacker.unpack(data_recv)
            except struct.error as emsg:
                print("Unpack data error: ", emsg)
                sys.exit(1)

            # TODO: update base pointer
            self.base = unpacked_data[0] + 1

            if self.timer is not None:
                self.timer.cancel()

            # TODO: if base is less than next_seq_num, restart the timer
            if self.base < self.next_seq_num:
                if self.timer is not None: self.timer.cancel()
                self.timer = threading.Timer(2, self.funcTimeout)
                self.timer.start()

    def sendPacket(self):
        while self.base <= len(self.pkt_data):
            while (
                self.next_seq_num < self.base + self.window_size
                and self.next_seq_num <= len(self.pkt_data)
            ):

                pkt = self.pkt_data[self.next_seq_num - 1]
                try:
                    # Pack data into binary
                    packed_data = self.packer.pack(
                        self.next_seq_num, bytes(pkt, encoding="utf-8")
                    )
                except struct.error as emsg:
                    print("Pack data error: ", emsg)
                    sys.exit(1)

                if lostPacket(self.next_seq_num, self.bound) is False:
                    try:
                        self.sender_socket.sendto(
                            packed_data, (self.RECV_IP, self.RECV_PORT)
                        )
                        print("Packet (seq num: %d) sent" % self.next_seq_num)
                    except error as emsg:
                        print("Socket send error: ", emsg)
                        sys.exit(1)

                # TODO: start the timer if the base equals the next_seq_num
                if self.base == self.next_seq_num:
                    if self.timer is not None: self.timer.cancel()
                    self.timer = threading.Timer(2, self.funcTimeout)
                    self.timer.start()

                # TODO: update next_seq_num
                self.next_seq_num += 1

        self.stop = True


def main(argv):
    SEND_IP = "127.0.0.1"
    SEND_PORT = 6666

    RECV_IP = "127.0.0.1"
    RECV_PORT = 7777
    BOUND = 0.1
    WINDOW_SIZE = 5

    try:
        sender_socket = socket(AF_INET, SOCK_DGRAM)
        sender_socket.bind((SEND_IP, SEND_PORT))
        sender_socket.settimeout(5)
    except error as emsg:
        print("Socket error: ", emsg)
        sys.exit(1)

    # define the format of send/receive packets
    try:
        packer = struct.Struct("I 32s")
        unpacker = struct.Struct("I")
    except struct.error as emsg:
        print("Struct error: ", emsg)
        sys.exit(1)

    try:
        f = open(argv[1])
        contents = f.read()
    except IOError as emsg:
        print("File IO error: ", emsg)
        sys.exit(1)

    pkt_data = [contents[i : i + 32] for i in range(0, len(contents), 32)]
    f.close()

    # GBN (Go-Back-N) protocol
    sender = RDTSend(
        sender_socket,
        pkt_data,
        RECV_IP,
        RECV_PORT,
        packer,
        unpacker,
        BOUND,
        WINDOW_SIZE,
    )

    # start sending data
    sender.send_data()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 RDTSend.py <filename>")
        sys.exit(1)
    main(sys.argv)
