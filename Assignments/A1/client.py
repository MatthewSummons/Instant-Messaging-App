'''
The Client program for the Instant Messaging Application
'''

import socket           # For sockets
import threading        # For threading.Thread
import sys              # For sys.argv
import os               # For forced exit

class ClientThread(threading.Thread):
    def __new__(cls, name) -> tuple[threading.Thread, int]:
        self = threading.Thread.__new__(cls)
        threading.Thread.__init__(self)
        self.name = name
        # Find an available port and bind the socket to it (for chat messaging)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('', 0))
        self.socket = sock
        return self, sock.getsockname()[1]

    def receive_msg(self, connectionSocket: socket.socket) -> str | None:
        response = ''
        while not response.endswith('\n'):
            try:
                response_buffer = connectionSocket.recv(1024)
            except KeyboardInterrupt:
                print("\nExiting...")
                sys.exit(1)
            except Exception as e:
                print("Connection to server lost. Exiting...")
                print(e)
                sys.exit(1)
            if len(response_buffer) == 0:
                connectionSocket.close()
                return None
            response += response_buffer.decode()
        return response
    
    def print_msg(self, sock: socket.socket, payload: list[str]) -> None:
        if payload is None:
            return sock.send("Error: No Message/n".encode())
        fmtStr = '\r' + f"{payload[0]} > {' '.join(payload[1:])}" + '\n' + f"{self.name} > "
        print(fmtStr, end='')
        sock.send("302 Message receipt successful\n".encode())

    
    def print_broadcast(self, sock: socket.socket, payload: list[str]) -> None:
        if payload is None:
            return sock.send("Error: No Message/n".encode())
        fmtStr = '\r' + f"{payload[0]} > {' '.join(payload[1:])}" + '\n' + f"{self.name} > "
        print(fmtStr, end='')
        sock.send("302 Message receipt successful\n".encode())

    def run(self) -> None:
        self.socket.listen(1)
        serverSocket, _ = self.socket.accept()

        msg: str | None = None
        while msg != "310 Bye bye\n":
            # Receive and verify the message to be non-null
            msg = self.receive_msg(serverSocket)
            if not(msg):  return self.end()
            msgList: list[str] = msg.split()   
            
            head, payload = msgList[0], msgList[1:]
            if head == "/from":
                self.print_msg(serverSocket, payload)
            elif head == "/broadcast":
                self.print_broadcast(serverSocket, payload)
            elif head == "/forceQuit":
                print("\nServer has been shut down. Exiting...")
                self.end()
                os._exit(1) # No other clean way to exit
            else:
                print(repr(head))
                print(msg)
        
    def end(self):
        self.socket.close()


class ClientMain:
    def __init__(self):
        self.name: str | None = None
    
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

    def receiveMsg(self, connectionSocket:socket.socket) -> str | None:
        try:
            return connectionSocket.recv(1024).decode()
        except KeyboardInterrupt:
            print("\nExiting...")
            sys.exit(1)
        except ConnectionResetError:
            print("Connection to server lost. Exiting...")
            sys.exit(1)

    
    def requestAuth(self, comm_socket:socket.socket) -> tuple[bool, str | None]:
        try:
            username = input("Please input your username: ")
            password = input("Please input your password: ")
        except KeyboardInterrupt:
            print("\nExiting...")
            return sys.exit(1)

        if len(username) == 0 or len(password) == 0:
            print("Empty username or password. Please try again.")
            return (False, None)

        # Send username and password to server
        request = f"/login {username} {password}\n"
        try:
            comm_socket.send(request.encode())
        except BrokenPipeError:
            print("Connection to server lost. Exiting...")
            sys.exit(1)
        
        
        # Await authentication response
        response = self.receiveMsg(comm_socket)
        if response == "101 Authentication successful\n":
            return (True, username)
        elif response == "102 Authentication Failed\n":
            print("\nAuthentication failed. Please try again.\n")
            return (False, None)
        elif response == "103 You are already logged in\n":
            print("\nAuthentication Failed. You are already logged in.\n")
            return (False, None)
        else:
            print("Unexpected response from server:", response)
            return (False, None)


    def establishConnection(self, comm_socket:socket.socket, port:str) -> bool | None:
        request = f"/port {port}\n"
        try:
            comm_socket.send(request.encode())
        except BrokenPipeError:
            print("Connection to server lost. Exiting...")
            return sys.exit(1)
        

        response = self.receiveMsg(comm_socket)
        if response == "202 Build connection failed\n":
            return print(response)
        elif response != "201 Build connection successful\n":
            return print("Unexpected Response:", response)
        return True


    def client_run(self) -> None:
        # Recieve IP and port of the server from from command line
        serverIP, serverPort_A = self.getCmdLineArgs()
        
        # Create a TCP socket to connect to the server
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:  clientSocket.connect( (serverIP, serverPort_A) )
        except ConnectionRefusedError:
            print("Server may be down, connection to server failed. Exiting...")
            sys.exit(1)
        except Exception as e:
            print("An unexpected error occurred:", e)
            sys.exit(1)


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
            return print("Failed to establish 2-way channel with server. Exiting...")
        
        response = ""
        while response != "310 Bye bye\n":
            try: request = input(f"{self.name} > ") + "\n"
            except KeyboardInterrupt:
                request = "/exit\n"
            
            # If blank line, don't send anything, ask client to input again
            if request == "\n":
                print("\nPlease input a message!\n")
                continue
            
            try: clientSocket.send(request.encode())
            except BrokenPipeError:
                print("Connection to server lost. Exiting...")
                chatThread.end()
                sys.exit(1)
            response = self.receiveMsg(clientSocket)
            print(f"\t{'[' + response[:-1] + ']':^100}")
        
        clientSocket.close()


if __name__ == '__main__':
    client = ClientMain()
    client.client_run()