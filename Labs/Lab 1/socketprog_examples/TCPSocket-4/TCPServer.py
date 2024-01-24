#!/usr/bin/python3

import socket
import threading

def thd_func(client):
    connectionSocket, addr = client    
    sentence = connectionSocket.recv(1024)
    capitalizedSentence = sentence.decode().upper()
    connectionSocket.send(capitalizedSentence.encode())
    connectionSocket.close()
    
serverPort = 12000

serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

serverSocket.bind( ("", serverPort) )

serverSocket.listen(5)

print("The server is ready to receive")

while True:
    
    client = serverSocket.accept()
    newthd = threading.Thread(target=thd_func, args=(client,))
    newthd.start()
    
serverSocket.close()