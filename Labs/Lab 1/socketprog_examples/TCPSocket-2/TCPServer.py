#!/usr/bin/python3

import socket

serverPort = 12000

serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

serverSocket.bind( ("", serverPort) )


serverSocket.listen(5)

print("The server is ready to receive")

while True:
    
    connectionSocket, addr = serverSocket.accept() 

    sentence = connectionSocket.recv(1024)

    capitalizedSentence = sentence.decode().upper()

    connectionSocket.send(capitalizedSentence.encode())

    connectionSocket.close()
    
serverSocket.close()

