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
        guess = ''
        while guess != self.secret:    
            # Obtain the client's complete guess
            response = ''
            while not response.endswith('\n'):
                response_buffer = connectionSocket.recv(1024)

                if len(response_buffer) == 0:
                    connectionSocket.close()

                response += response_buffer.decode()
            print("Received guess: ", response, end="")
            # Game Logic
            try:
                guess = int(response)
            except:
                connectionSocket.close()
            
            msg = None
            if guess < self.secret:
                msg = "Too low"
            elif guess > self.secret:
                msg = "Too high"
            else:
                msg = "You win!"
            
            try:
                connectionSocket.send((msg + "\n").encode())
            except:
                connectionSocket.close()
            
        connectionSocket.close()






















class ServerMain:
    def __init__(self):
        self.secret = random.randint(1, 100)

    def server_run(self):
        # Step 3: set up `serverSocket` that listens for TCP connections on port 12000
        # Hint: refer to socketprog_examples/TCPSocket-5
        serverPort = 12000
        serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)    # Use TCP
        serverSocket.bind( ("", serverPort) )
        serverSocket.listen(5)      # Backlog of 5

        print("Game started! The secret is", self.secret)

        while True:
            # Step 3: accept a connection and launch a thread to handle the connection. Pass appropriate arguments to the thread constructor
            client = serverSocket.accept()
            t = ServerThread(client, self.secret)
            t.start()






if __name__ == '__main__':
    server = ServerMain()
    server.server_run()
