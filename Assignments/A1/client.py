'''
The Client program for the Instant Messaging Application
'''

import socket           # For sockets
import threading        # For threading.Thread
import sys              # For sys.argv

class ClientThread(threading.Thread):
    def __new__(cls, name) -> tuple[threading.Thread, int]:
        self = threading.Thread.__new__(cls)
        threading.Thread.__init__(self)
        self.name = name
        # Find an available port and bind the socket to it (for chat messaging)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('', 0))
        self.socket: socket.socket = sock
        return self, sock.getsockname()[1]

    def receive_msg(self, connectionSocket) -> str:
        return connectionSocket.recv(1024).decode()
    
    def print_chat_msg(self, sock: socket.socket, payload: list[str]) -> None:
        if payload is None:
            return sock.send("Error: No Message/n".encode())
        # FIXME: Fix the order of the chatters
        fmtStr = '\r' + f"{payload[0]} > {' '.join(payload[1:])}" + '\n' + f"{self.name} > "
        print(fmtStr, end='')
        sock.send("302 Message receipt successful\n".encode())

    def run(self) -> None:
        self.socket.listen(1)
        serverSocket, _ = self.socket.accept()

        msg = self.receive_msg(serverSocket).split()
        while msg != "310 Bye bye\n":
            head, payload = msg[0], msg[1:]
            if head == "/from":
                self.print_chat_msg(serverSocket, payload)
            else:
                print(repr(head))
                print(msg)
            msg = self.receive_msg(serverSocket).split()
        
    
    def end(self):
        self.socket.close()

class ClientMain:
    def __init__(self):
        self.name = None
    
    def getCmdLineArgs(self) -> tuple[str, int]:
        # Check if the correct number of arguments were passed
        if len(sys.argv) != 3:
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

    
    def requestAuth(self, comm_socket:socket.socket) -> tuple[bool, str | None]:
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
            print("Unexpected response from server:")
            print(response)
            return (False, None)


    def establishConnection(self, comm_socket:socket.socket, port:str) -> bool | None:
        request = f"/port {port}\n"
        comm_socket.send(request.encode())
        
        response = self.receiveMsg(comm_socket)
        if response == "202 Build connection failed\n":
            return print(response)
        elif response != "201 Build connection successful\n":
            return print("Unexpected Response:", response)
        return True


    def client_run(self):
        # Recieve IP and port of the server from from command line
        serverIP, serverPort_A = self.getCmdLineArgs()
        
        # Create a TCP socket to connect to the server
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientSocket.connect( (serverIP, serverPort_A) )

        # Authenticate User
        authenticated = False
        while not authenticated:
            authenticated, self.name = self.requestAuth(clientSocket)
        print(f"Authentication Successful. Welcome {self.name}!")

        # Spawn a new thread to handle chat message communication, let main thread handle commands
        chatThread, serverPort_B = ClientThread(self.name)
        chatThread.start()
        # Establish a connection to the chat server on port: {serverPort_B}
        ret = self.establishConnection(clientSocket, serverPort_B)

        if ret is None:
            chatThread.end()
            return print("Connection failed. Exiting...")
        
        response = True
        while response != "310 Bye bye\n":
            request = input(f"{self.name} > ") + "\n"
            clientSocket.send(request.encode())
            response = self.receiveMsg(clientSocket)
            print()
            print(response)
        
        # TODO: Clean up client and its threads
        # chatThread.terminate()
        clientSocket.close()


if __name__ == '__main__':
    client = ClientMain()
    client.client_run()