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

    def receiveMsg(self, connectionSocket):
        return connectionSocket.recv(1024).decode()


    def requestAuth(self, comm_socket:socket.socket) -> tuple[bool, str]:
        username = input("Please input your username: ")
        password = input("Please input your password: ")

        if len(username) == 0 or len(password) == 0:
            print("Empty username or password. Please try again.")
            return (False, None)

        # Send username and password to server
        request = f"/login {username} {password}\n"
        comm_socket.send(request.encode())
        
        # Await authentication response
        response = self.receiveMsg(comm_socket)
        if response == "101 Authentication successful\n":
            return (True, username)
        elif response == "102 Authentication Failed\n":
            print("\nAuthentication failed. Please try again.\n")
            return (False, None)
        else:
            print(f"Unexpected response from server: {response}")
            return (False, None)


    def client_run(self):
        # Recieve IP and port of the server from from command line
        serverIP, serverPort = self.getCmdLineArgs()
        
        # Create a TCP socket to connect to the server
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientSocket.connect( (serverIP, serverPort) )

        # Authenticate User
        authenticated, usr = False, None
        while not authenticated:
            authenticated, usr = self.requestAuth(clientSocket)
        print(f"Authentication Successful. Welcome {usr}!")


if __name__ == '__main__':
    client = ClientMain()
    client.client_run()