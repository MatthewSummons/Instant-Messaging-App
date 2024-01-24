#!/usr/bin/python3

from socket import *

serverPort = 12000

serverSocket = socket(AF_INET, SOCK_DGRAM)

serverSocket.bind( ("", serverPort) )

print("The server is ready to receive")

while True:
    
    sentence, clientAddress = serverSocket.recvfrom(1024)

    capitalizedSentence = sentence.decode().upper()

    serverSocket.sendto(capitalizedSentence.encode(), clientAddress)
    
serverSocket.close()