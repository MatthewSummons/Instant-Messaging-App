#!/usr/bin/python3

import socket

clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

serverName = "localhost"

serverPort = 12000

clientSocket.connect( (serverName, serverPort) )

# Get input for sending
sentence = input("Input a lowercase sentence:")

clientSocket.send(sentence.encode())

modifiedSentence = clientSocket.recv(1024)

print("From Server:", modifiedSentence.decode())

clientSocket.close()
