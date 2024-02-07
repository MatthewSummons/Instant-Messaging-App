'''
The Server Program for the Instant Messaging Application
'''

import socket           # For sockets
import threading        # For threading.Thread, threading.Lock
import sys              # For sys.argv

class ServerThread(threading.Thread):
    def __init__(self, client, authPath: str, lock: threading.Lock, \
                 onlineHashset: dict[str, str], sockMutex: threading.Lock):
        
        threading.Thread.__init__(self)
        self.name: str = None
        # Socket_A is used for control messages, Socket_B is used for chat messages
        self.socket_A: socket.socket = client[0]
        self.socket_B: socket.socket = None
        # The path of the file containing the username/password pairs
        self.authPath: str = authPath
        # The list of online users and a lock to provide thread safety
        self.onlineHashMutex: threading.Lock = lock
        self.onlineHashset: dict[str, str] = onlineHashset
        self.sockMutex: threading.Lock = sockMutex


    def receive_msg(self, connectionSocket) -> str:
        return connectionSocket.recv(1024).decode()

    
    def authenticate_user(self, payload: list[str, str]):
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

    def attempt_log_user(self, username) -> str:
        authSuccess = False
        self.onlineHashMutex.acquire()
        if username in self.onlineHashset: authSuccess = False
        else:
            self.onlineHashset[username] = None
            authSuccess = True
        self.onlineHashMutex.release()
        
        if authSuccess:
            return "101 Authentication successful\n"
        return "103 You are already logged in\n"
      

    def build_connection(self, payload:list[str]) -> socket.socket:
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
        self.socket_A.send("201 Build connection successful\n".encode())
        print(f"User {self.name} has connected to the chat server on port: {payload[0]}")


    def list_online_users(self):
        self.onlineHashMutex.acquire()
        response = "301 " + " ".join(list(self.onlineHashset.keys())) + "\n"
        self.onlineHashMutex.release()
        
        self.socket_A.send(response.encode())
        print("Sent list of online users to: ", self.name)
    

    def send_message_to(self, payload: list[str, str]):
        if len(payload) != 2:
            return self.socket_A.send("304 Message delivery failed\n".encode())

        # Check if target receiver is online
        sendingSock, response = None, None
        self.sockMutex.acquire()
        if payload[0] in self.onlineHashset:
            sendingSock = self.onlineHashset[payload[0]]        
        if sendingSock is not None:
            sendingSock.send(f"/from {self.name} {payload[1]}\n".encode())
            response = self.receive_msg(sendingSock)
        self.sockMutex.release()

        if sendingSock is None:
            self.socket_A.send("304 Message delivery failed\n".encode())
        
        
        print(response)

    
    def close(self):
        print("Logging out user: ", self.name)
        self.onlineHashMutex.acquire()
        self.onlineHashset.pop(self.name)
        self.onlineHashMutex.release()

        self.socket_A.close()
        self.socket_B.close()

    def run(self):
        # Receive and handle messages from client
        msgArr = self.receive_msg(self.socket_A).split()
        while msgArr:            
            head, payload = msgArr[0], msgArr[1:]
            match head:
                case "/login":
                    self.authenticate_user(payload)
                case "/port":
                    self.build_connection(payload)
                case "/list":
                    self.list_online_users()
                # TODO: Still Implementing
                case "/to":
                    self.send_message_to(payload)
                case "/toall":
                    pass  # TODO: Implement
                case "/exit" | "exit" | "quit" | "logout" | "logoff" | "bye":
                    self.socket_A.send("310 Bye bye\n".encode())
                case _:
                    print("Unrecognized message: ", head, payload)
                    self.socket_A.send("401 Unrecognized message\n".encode())
            msgArr = self.receive_msg(self.socket_A).split()

        self.close()
        




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

        onlineHashset, hashMutex, sockMutex  = {}, threading.Lock(), threading.Lock()
        while True:
            client = serverSocket.accept()
            print("Received connection. Spawning a new thread to handle it.")
            thread = ServerThread(client, path, hashMutex, onlineHashset, sockMutex)
            thread.start()



if __name__ == '__main__':
    server = ServerMain()
    server.server_run()