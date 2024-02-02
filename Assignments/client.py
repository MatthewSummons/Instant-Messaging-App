'''
The Client program for the Instant Messaging Application
'''

import socket           # For sockets
import threading        # For threading.Thread
import sys              # For sys.argv

# TODO: Build this later
class ClientThread(threading.Thread):
    pass

class ClientMain:
    def getCmdLineArgs(self) -> (str, int):
        # Check if the correct number of arguments were passed
        if (len(sys.argv) != 3):
            print("Usage: python3 client.py <serverIP> <serverPort>")
            sys.exit(1)
        # Check if the serverPort is an integer and is valid
        serverIP, serverPort = sys.argv[1], None
        try:
            serverPort = int(sys.argv[2])
        except ValueError:
            print("Usage: serverPort must be an integer")
            sys.exit(1)
        if not (0 <= serverPort <= 65535):
            print("Usage: serverPort must be in range [0, 65535]")
            sys.exit(1)
        
        return serverIP, serverPort

    # TODO: Build this
    def recvMsg(self, comm_socket):
        pass

    def requestAuth(self, comm_socket) -> bool:
        username = input("Please input your username: ")
        password = input("Please input your password: ")

        # Send username and password to server
        request = f"/login {username} {password}\n"
        comm_socket.send(request.encode())

        return False

        

    def client_run(self):
        # Recieve IP and port of the server from from command line
        serverIP, serverPort = self.getCmdLineArgs()
        
        # Create a TCP socket to connect to the server
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientSocket.connect( (serverIP, serverPort) )

        # Authenticate User
        authenticated = False
        while not authenticated:
            authenticated = self.requestAuth(clientSocket)


if __name__ == '__main__':
    client = ClientMain()
    client.client_run()