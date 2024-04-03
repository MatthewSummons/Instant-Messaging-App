#!/usr/bin/python3

from socket import *
import sys
import struct
import random


# simulate ack loss
def lostACK(seq_num, bound=0.1):
    prob = random.random()
    if prob < bound:
        print("ACK %d sent from Receiver lost" % seq_num)
        return True
    else:
        return False


class RDTReceive:
    def __init__(
        self,
        receiver_socket,
        f,
        SEND_IP,
        SEND_PORT,
        packer,
        unpacker,
        bound,
    ) -> None:
        self.receiver_socket = receiver_socket
        self.f = f
        self.SEND_IP = SEND_IP
        self.SEND_PORT = SEND_PORT
        self.packer = packer
        self.unpacker = unpacker
        self.bound = bound

        self.expt_seq_num = 1
        self.latest_seq_num = 0

    def recv_data(self):

        packed_data = None
        while True:
            try:
                data, _ = self.receiver_socket.recvfrom(1024)
            except timeout:
                print("Socket timeout, terminate the receiver program.")
                break

            # unpack received data
            try:
                unpacked_data = self.unpacker.unpack(data)
            except struct.error as emsg:
                print("Unpack data error: ", emsg)
                sys.exit(1)

            # if packet received has expected seq_num, decode and write the content into
            # the aboved opened file
            if unpacked_data[0] == self.expt_seq_num:
                content = unpacked_data[1].decode()

                # write the content into a file
                try:
                    self.f.write(content)
                except IOError as emsg:
                    print("File IO error: ", emsg)
                    sys.exit(1)

                print("Receive expected packet with seq num: %d" % self.expt_seq_num)

                try:
                    packed_data = self.packer.pack(self.expt_seq_num)
                except struct.error as emsg:
                    print("Pack data error: ", emsg)
                    sys.exit(1)

                # send the ACK to the sender if lostACK() returns false
                if lostACK(self.expt_seq_num, self.bound) is False:
                    try:
                        self.receiver_socket.sendto(
                            packed_data, (self.SEND_IP, self.SEND_PORT)
                        )
                    except error as emsg:
                        print("Socket send error: ", emsg)
                        sys.exit(1)
                    print("Cumulative ACK %d sent to the Sender" % self.expt_seq_num)

                # change expected and latest received sequence number for next packet
                self.expt_seq_num += 1
                self.latest_seq_num = unpacked_data[0]

            else:  # if packet received has wrong seq_num, resend previous ack
                print(
                    "Receive unexpected packet with wrong seq_num %d, resending latest ACK ..."
                    % unpacked_data[0]
                )

                # create corresponding ACK
                try:
                    packed_data = self.packer.pack(self.latest_seq_num)
                except struct.error as emsg:
                    print("Pack data error: ", emsg)
                    sys.exit(1)

                if lostACK(self.latest_seq_num, self.bound) is False:
                    try:
                        self.receiver_socket.sendto(
                            packed_data, (self.SEND_IP, self.SEND_PORT)
                        )
                    except error as emsg:
                        print("Socket send error: ", emsg)
                        sys.exit(1)
                    print("Latest ACK %d resent to the Sender" % self.latest_seq_num)

        self.f.close()
        self.receiver_socket.close()


def main(argv):
    SEND_IP = "127.0.0.1"
    SEND_PORT = 6666

    RECV_IP = "127.0.0.1"
    RECV_PORT = 7777
    BOUND = 0.1

    try:
        receiver_socket = socket(AF_INET, SOCK_DGRAM)
        receiver_socket.bind((RECV_IP, RECV_PORT))
    except error as emsg:
        print("Socket error: ", emsg)
        sys.exit(1)

    # define the format of received/sent packets
    try:
        packer = struct.Struct("I")
        unpacker = struct.Struct("I 32s")
    except struct.error as emsg:
        print("Struct error: ", emsg)
        sys.exit(1)

    try:
        f = open("recv.txt", "w")
    except IOError as emsg:
        print("File IO error: ", emsg)
        sys.exit(1)

    # terminate the program if timeout - 5 seconds
    receiver_socket.settimeout(5)

    receiver = RDTReceive(
        receiver_socket,
        f,
        SEND_IP,
        SEND_PORT,
        packer,
        unpacker,
        BOUND,
    )

    # start receiving data
    receiver.recv_data()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        print("Usage: python3 RDTReceive.py")
        sys.exit(1)
    main(sys.argv)
