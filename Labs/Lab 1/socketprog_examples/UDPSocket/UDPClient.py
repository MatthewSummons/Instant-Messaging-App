#!/usr/bin/python3

from socket import *

clientSocket = socket(AF_INET, SOCK_DGRAM)

serverName = "localhost"

serverPort = 12000

# Get input for sending
sentence = input("Input a lowercase sentence:")

clientSocket.sendto(sentence.encode(), (serverName, serverPort))

modifiedSentence, serverAddress = clientSocket.recvfrom(1024)

print("From Server:", modifiedSentence.decode())

clientSocket.close()
