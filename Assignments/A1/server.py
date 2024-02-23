'''
The Server Program for the Instant Messaging Application
'''

import socket           # For sockets
import threading        # For threading.Thread, threading.Lock
import sys              # For sys.argv

class ServerThread(threading.Thread):
    def __init__(
        self,
        client,
        authPath: str,
        hashMutex: threading.Lock,
        onlineHashset: dict[str, socket.socket | None],
        sockMutex: threading.Lock
        ) -> None:
        
        threading.Thread.__init__(self)
        self.name: str = "" 
        # Socket_A is used for control messages, Socket_B is used for chat messages
        self.socket_A: socket.socket = client[0]
        self.socket_B: socket.socket | None = None
        # The path of the file containing the username/password pairs
        self.authPath: str = authPath
        # The list of online users and a lock to provide thread safety
        self.onlineHashMutex: threading.Lock = hashMutex
        self.onlineHashset: dict[str, socket.socket | None] = onlineHashset
        self.sockMutex: threading.Lock = sockMutex
        # Flag to force close the connection
        self.forceQuit: bool = False
        self.socket_A.settimeout(2)


    def receive_msg(self, connectionSocket:socket.socket) -> str:
        return connectionSocket.recv(1024).decode()

    def authenticate_user(self, payload: list[str]):
        if len(payload) != 2:
            return self.socket_A.send("102 Authentication Failed\n".encode())
        
        sentUsername, sentPassword = payload
        with open(self.authPath, 'r') as authFile:
            for line in authFile:
                username, password = line.split()
                if (username == sentUsername and password == sentPassword):
                    self.name = username
                    status = self.attempt_log_user(self.name)
                    return self.socket_A.send(status.encode())
        return self.socket_A.send("102 Authentication Failed\n".encode())

    def attempt_log_user(self, username:str) -> str:
        authSuccess = False
        self.onlineHashMutex.acquire()
        if username in self.onlineHashset: authSuccess = False
        else:
            self.onlineHashset[username] = None
            authSuccess = True
        self.onlineHashMutex.release()
        
        if authSuccess:
            return "101 Authentication successful\n"
        print("User", username, "is already logged in and attempted to log in again")
        return "103 You are already logged in\n"
      

    def build_connection(self, payload:list[str]) -> int | None:
        if len(payload) != 1 or not(payload[0].isnumeric()):
            return self.socket_A.send("202 Build connection failed\n".encode())
        # Establish a socket to send chat messages through
        clientIP, _ = self.socket_A.getsockname()
        self.socket_B = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_B.connect((clientIP, int(payload[0])))
        
        # Update the reference to the socket in the onlineHashset
        self.onlineHashMutex.acquire()
        self.onlineHashset[self.name] = self.socket_B
        self.onlineHashMutex.release()

        # Report success to the client's main thread
        print(f"User {self.name} has connected to the chat server on port: {payload[0]}")
        return self.socket_A.send("201 Build connection successful\n".encode())


    def list_online_users(self):
        self.onlineHashMutex.acquire()
        response = "301 " + " ".join(list(self.onlineHashset.keys())) + "\n"
        self.onlineHashMutex.release()
        
        self.socket_A.send(response.encode())
        print("Sent list of online users to:", self.name)
    

    def send_message(self, payload: list[str]):
        if payload[0] == self.name:
            return self.socket_A.send("304 Message delivery failed\n".encode())
        # Check if target receiver is online
        sendingSock, response = None, None
        self.sockMutex.acquire()
        if payload[0] in self.onlineHashset:
            sendingSock = self.onlineHashset[payload[0]]
        if sendingSock is not None:
            try:
                sendingSock.send(f"/from {self.name} {' '.join(payload[1:])}\n".encode())
                response = self.receive_msg(sendingSock)
            except Exception as e: print(e)
        self.sockMutex.release()

        if response == "302 Message receipt successful\n":
            return self.socket_A.send("303 Message delivery successful\n".encode())
        
        # If sendingSock is None or response is not 302
        self.socket_A.send("304 Message delivery failed\n".encode())


    def broadcast_message(self, payload: list[str]):
        responseBin: list[str] = []
        self.onlineHashMutex.acquire()
        numOnlineUsers = len(self.onlineHashset)
        for username, clientSock_B in self.onlineHashset.items():
            if username != self.name and clientSock_B is not None:
                try:
                    clientSock_B.send(f"/broadcast {self.name} {' '.join(payload)}\n".encode())
                    responseBin.append(self.receive_msg(clientSock_B))
                except Exception as e: print(e)
        self.onlineHashMutex.release()

        if len(responseBin) != numOnlineUsers - 1:
            return self.socket_A.send("304 Message delivery failed\n".encode())
        
        for response in responseBin:
            if response != "302 Message receipt successful\n":
                return self.socket_A.send("304 Message delivery failed\n".encode())

        self.socket_A.send("303 Message delivery successful\n".encode())
    
    def forceClose(self):
        try:
            self.sockMutex.acquire()
            self.socket_B.send("/forceQuit\n".encode())
            self.sockMutex.release()
        except Exception as e:
            print("Failed to send a disconnect message to the client")
            print(e)
        self.close()

    def close(self):
        print("Closing a connection:")
        if self.name:
            print("  Logging out user:", self.name)
            self.onlineHashMutex.acquire()
            self.onlineHashset.pop(self.name)
            self.onlineHashMutex.release()
            print("  User logged out")
        
        self.socket_A.close()
        if self.socket_B:
            self.socket_B.close()
        print("  Sockets closed")

    def run(self) -> None:
        # Receive and handle messages from client
        msgArr = ['', '']
        while msgArr:            
            if self.forceQuit: return self.forceClose()
            
            try:
                msgArr = self.receive_msg(self.socket_A).split()
            # Check for forceQuit every 2 seconds
            except TimeoutError: continue
            except Exception as e: return self.close()
            
            # Handle user quitting during login and authetication
            if not(msgArr):
                return self.close()


            if self.name: print(f"Received message from {self.name}: ", msgArr)
            else: print("A first message from a client was received: ", msgArr)
            head, payload = msgArr[0], msgArr[1:]
            match head:
                case "/login":
                    self.authenticate_user(payload)
                case "/port":
                    self.build_connection(payload)
                case "/list":
                    self.list_online_users()
                case "/to":
                    self.send_message(payload)
                case "/toall":
                    self.broadcast_message(payload)
                case "/exit" | "exit" | "quit" | "logout" | "logoff" | "bye":
                    self.socket_A.send("310 Bye bye\n".encode())
                case _:
                    print(f"Unrecognized message from {self.name}: ", head, payload)
                    self.socket_A.send("401 Unrecognized message\n".encode())

        self.close()
        

# Main thread handles receiving connections and spawning new threads (besides getting cmdline args)
class ServerMain:
    def getCmdLineArgs(self) -> tuple[int, str]:
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
    
    def server_run(self) -> None:
        # Recieve port and path to the username/password file from command line
        serverPort, path = self.getCmdLineArgs()
        
        # Create a TCP socket
        serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            serverSocket.bind( ("", serverPort) )
        except OSError as e:
            return print(e)
        
        serverSocket.listen(5)

        print("The server is ready to receive!")

        threadSet: set[ServerThread] = set()
        onlineHashset: dict[str, socket.socket | None] = {}
        hashMutex, sockMutex  = threading.Lock(), threading.Lock()
        while True:
            try: client = serverSocket.accept()
            except KeyboardInterrupt:
                print("\rServer is now shutting down.")
                try:
                    for thrd in threadSet:
                        thrd.forceQuit = True
                except KeyboardInterrupt:
                    print("Closing all connections, please wait...")

                    
                sys.exit(0)
            
            print("Received connection. Spawning a new thread to handle it.")
            thread = ServerThread(client, path, hashMutex, onlineHashset, sockMutex)
            threadSet.add(thread)
            thread.start()



if __name__ == '__main__':
    server = ServerMain()
    server.server_run()