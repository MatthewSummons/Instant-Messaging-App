'''
The Server Program for the Instant Messaging Application
'''

import socket           # For sockets
import threading        # For threading.Thread
import sys              # For sys.argv

class ServerThread(threading.Thread):
    def __init__(self, client, authPath:str):
        threading.Thread.__init__(self)
        self.client = client
        self.authPath = authPath
    

    def receiveMsg(self, connectionSocket):
        return connectionSocket.recv(1024).decode()

    
    
    def authenticateUser(self, connectionSocket):        
        # username, password = connectionSocket.recv(1024).decode()

        with open(self.authPath, 'r') as authFile:
            for line in authFile:
                username, password = line.split()
                if (username == self.username and password == self.password):
                    connectionSocket.send("Login Successful".encode())
                    return True

    def run(self):
        connectionSocket, addr = self.client
        print(addr)
        # Receive and handle messages from client
        # while True:

        # TODO: Authenticate user

        
        self.authenticateUser(connectionSocket)





class ServerMain:
    def getCmdLineArgs(self) -> (int, str):
        # Check if the correct number of arguments were passed
        if (len(sys.argv) != 3):
            print("Usage: python3 server.py <serverPort> <path>")
            sys.exit(1)
        # Check if the serverPort is an integer and is valid
        serverPort = None
        try:
            serverPort = int(sys.argv[1])
        except ValueError:
            print("Usage: serverPort must be an integer")
            sys.exit(1)
        if not (0 <= serverPort <= 65535):
            print("Usage: serverPort must be in range [0, 65535]")
            sys.exit(1)
        
        path = sys.argv[2]
        return serverPort, path
    
    def server_run(self):
        # Recieve port and path to the username/password file from command line
        serverPort, path = self.getCmdLineArgs()
        
        # Create a TCP socket
        serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serverSocket.bind( ("", serverPort) )
        serverSocket.listen(5)

        print("The server is ready to receive!")

        while True:
            client = serverSocket.accept()
            thread = ServerThread(client, path)
            thread.start()



if __name__ == '__main__':
    server = ServerMain()
    server.server_run()