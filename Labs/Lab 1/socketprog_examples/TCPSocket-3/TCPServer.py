#!/usr/bin/python3

import socket

serverPort = 12000

serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

serverSocket.bind( ("", serverPort) )


serverSocket.listen(5)

print("The server is ready to receive")

while True:
    
    connectionSocket, addr = serverSocket.accept() 

    try:
        sentence = connectionSocket.recv(1024)
    except socket.error as err:
    	print("Recv error: ", err)
        
    if sentence:
        capitalizedSentence = sentence.decode().upper()

        connectionSocket.send(capitalizedSentence.encode())

    else:
	    print("Connection is broken")
    
    connectionSocket.close()

