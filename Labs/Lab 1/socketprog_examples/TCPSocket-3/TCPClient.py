#!/usr/bin/python3

import socket
import sys

clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

serverName = "localhost"

serverPort = 12000

try:
    clientSocket.connect( (serverName, serverPort) )
except socket.error as err:
	print("Connection error: ", err)
	sys.exit(1)
    
# Get input for sending
try:
    sentence = input("Input a lowercase sentence:")
except:
	print("Terminated abnormally!!")
	clientSocket.close()
	sys.exit(1)

clientSocket.send(sentence.encode())

modifiedSentence = clientSocket.recv(1024)

print("From Server:", modifiedSentence.decode())

clientSocket.close()
