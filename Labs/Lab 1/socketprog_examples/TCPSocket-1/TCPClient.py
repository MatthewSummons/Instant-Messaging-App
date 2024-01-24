#!/usr/bin/python3

from socket import *

clientSocket = socket(AF_INET, SOCK_STREAM)

serverName = "localhost"

serverPort = 12000

clientSocket.connect( (serverName, serverPort) )

# Get input for sending
sentence = input("Input a lowercase sentence:")

clientSocket.send(sentence.encode())

modifiedSentence = clientSocket.recv(1024)

print("From Server:", modifiedSentence.decode())

clientSocket.close()
