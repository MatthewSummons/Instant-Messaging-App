#!/usr/bin/python3

import socket

clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

serverName = "localhost"

serverPort = 12000

clientSocket.connect( (serverName, serverPort) )

try:
    while True:
        guess = input("Input a guess: ")
        guess += '\n'

        clientSocket.send(guess.encode())

        response = ''
        while not response.endswith('\n'):
            response_buffer = clientSocket.recv(1024)

            if len(response_buffer) == 0:
                raise Exception("Server closed connection")

            response += response_buffer.decode()

        print(response)

        if response == "You win!\n":
            break
finally:
    clientSocket.close()
