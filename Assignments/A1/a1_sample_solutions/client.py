import sys
import socket
import threading

# reads a line of string from `socket`
def recv_line(socket):
    data = ''
    while not data.endswith('\n'):
        buffer = socket.recv(1024)
        if len(buffer) == 0:
            raise Exception("Server closed connection")
        data += buffer.decode()
    print(data.strip())
    return data

# the "thread Tb" that handles the messages from Lb
class ThreadB(threading.Thread):
    def __init__(self, serverSocket):
        threading.Thread.__init__(self)
        self.serverSocket = serverSocket

    def run(self):
        socketB, address = self.serverSocket.accept()
        self.serverSocket.close()

        try:
            while True:
                data = recv_line(socketB)
                socketB.sendall("302 Message receipt successful\n".encode())
        except:
            print("Error occurs when receiving message from Lb")

def main(ip, port):
    try:
        socketA = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socketA.connect((ip, port))

        # 1. authentication
        while True:
            username = input("Please input your user name: ").strip()
            password = input("Please input your password: ").strip()
            socketA.sendall(f"/login {username} {password}\n".encode())

            response = recv_line(socketA)
            if response == "101 Authentication successful\n":
                break
    except:
        print("Failed to connect to the server")
        socketA.close()
        return

    # 2. setup Lb
    try:
        serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serverSocket.bind( ("", 0) )
        serverSocket.listen(1)

        thread = ThreadB(serverSocket)
        thread.start()

        address, port = serverSocket.getsockname()
        socketA.sendall(f"/port {port}\n".encode())
        response = recv_line(socketA)
        assert response == "201 Build connection successful\n"
    except:
        print("Failed to setup Lb")
        socketA.close()
        return

    # 3. handle commands
    try:
        while True:
            command = input("").strip()
            socketA.sendall(f"{command}\n".encode())
            response = recv_line(socketA)

            if command == "/exit" and response == "310 Bye bye\n":
                return
    finally:
        socketA.close()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: python3 client.py <ip> <port>")
        exit()

    main(sys.argv[1], int(sys.argv[2]))
