import sys
import socket
import threading

# reads a line of string from `socket`
def recv_line(socket):
    data = ''
    while not data.endswith('\n'):
        buffer = socket.recv(1024)
        if len(buffer) == 0:
            raise Exception("Client closed connection")
        data += buffer.decode()
    print(data.strip())
    return data

class ServerThread(threading.Thread):
    def __init__(self, users, online_users, socketA):
        threading.Thread.__init__(self)
        self.socketA = socketA # the socket for La
        self.socketB = None # the socket for Lb
        self.lock = threading.Lock() # locks socketB to prevent out-of-order response if two users send to the same user concurrently
        self.users = users # the global user dict
        self.online_users = online_users # the global list of the user_names of online users
        self.user_name = None # the user name of the client served by this thread

    def run(self):
        try:
            while True:
                command = recv_line(self.socketA)

                if command.startswith("/login "):
                    try:
                        user_name, password = command.strip().split(' ')[1:]
                        assert self.users[user_name].password == password
                    except:
                        self.socketA.sendall("401 Authentication failed\n".encode())
                    else:
                        self.socketA.sendall("101 Authentication successful\n".encode())
                        # login successful, update the user_name and online_users
                        self.user_name = user_name
                        self.users[user_name].thread = self
                        self.online_users.append(self.user_name)

                elif command.startswith("/port "):
                    try:
                        port = int(command.split(' ')[1])
                        # build Lb connection to the client
                        self.socketB = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        self.socketB.connect( ("", port) )
                    except:
                        self.socketA.sendall("202 Build connection failed\n".encode())
                    else:
                        self.socketA.sendall("201 Build connection successful\n".encode())

                elif command == "/list\n":
                    response = "301"
                    for user_name in self.online_users:
                        response += ' ' + user_name
                    response += '\n'
                    self.socketA.sendall(response.encode())

                elif command.startswith("/to "):
                    try:
                        target_username, chat_content = command.split(' ', 2)[1:]
                        target_user = self.users[target_username]
                        with target_user.thread.lock:
                            target_user.thread.socketB.sendall(f"/from {self.user_name} {chat_content}".encode())
                            response = recv_line(target_user.thread.socketB)
                        assert response == "302 Message receipt successful\n"
                    except:
                        self.socketA.sendall("304 Message delivery failed\n".encode())
                    else:
                        self.socketA.sendall("303 Message delivery successful\n".encode())

                elif command.startswith("/toall "):
                    try:
                        chat_content = command.split(' ', 1)[1]
                        for user_name in self.online_users:
                            # skip sending to self
                            if user_name == self.user_name:
                                continue
                            target_user = self.users[user_name]
                            with target_user.thread.lock:
                                target_user.thread.socketB.sendall(f"/broadcastfrom {self.user_name} {chat_content}".encode())
                                response = recv_line(target_user.thread.socketB)
                            assert response == "302 Message receipt successful\n"
                    except:
                        self.socketA.sendall("304 Message delivery failed\n".encode())
                    else:
                        self.socketA.sendall("303 Message delivery successful\n".encode())

                elif command == "/exit\n":
                    self.socketA.sendall("310 Bye bye\n".encode())
                    return # also triggers the finally block to clean up

                else:
                    self.socketA.sendall("401 Unrecognized message\n".encode())

        finally:
            self.users[self.user_name].thread = None
            if self.user_name in self.online_users:
                self.online_users.remove(self.user_name)
            self.socketA.close()
            if self.socketB != None:
                self.socketB.close()

class User:
    def __init__(self, password):
        self.password = password
        self.thread = None # the thread that is serving this user. None if the user is offline

def main(port, users_file):
    users = {}
    for line in open(users_file):
        user_name, password = line.strip().split(' ')
        users[user_name] = User(password)

    print("Starting server on port", port)
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.bind( ("", port) )
    serverSocket.listen(5)

    online_users = []

    try:
        while True:
            clientSocket, address = serverSocket.accept()
            print("Client connected from", address)
            thread = ServerThread(users, online_users, clientSocket)
            thread.start()
    finally:
        serverSocket.close()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 server.py <port> <users_file>")
        exit()

    main(int(sys.argv[1]), sys.argv[2])
