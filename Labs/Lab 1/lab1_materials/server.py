#!/usr/bin/python3

import random
import socket
import threading

class ServerThread(threading.Thread):
    def __init__(self, client, secret):
        threading.Thread.__init__(self)
        self.client = client
        self.secret = secret

    def run(self):
        connectionSocket, addr = self.client

        # Step 4: read the client's guesses and send responses until the client guesses correctly





















class ServerMain:
    def __init__(self):
        self.secret = random.randint(1, 100)

    def server_run(self):
        # Step 3: set up `serverSocket` that listens for TCP connections on port 12000
        # Hint: refer to socketprog_examples/TCPSocket-5




        print("Game started! The secret is", self.secret)

        while True:
            # Step 3: accept a connection and launch a thread to handle the connection. Pass appropriate arguments to the thread constructor






if __name__ == '__main__':
    server = ServerMain()
    server.server_run()
