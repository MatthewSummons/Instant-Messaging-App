#!/usr/bin/python3

import socket
import threading

class ServerThread(threading.Thread):
	def __init__(self, client):
		threading.Thread.__init__(self)
		self.client = client

	def run(self):
		connectionSocket, addr = self.client    
		sentence = connectionSocket.recv(1024)
		capitalizedSentence = sentence.decode().upper()
		connectionSocket.send(capitalizedSentence.encode())
		connectionSocket.close()

class ServerMain:
	def server_run(self):  
		serverPort = 12000
		serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		serverSocket.bind( ("", serverPort) )
		serverSocket.listen(5)
		print("The server is ready to receive")
		while True:
			client = serverSocket.accept()
			t = ServerThread(client)
			t.start()

if __name__ == '__main__':
	server = ServerMain()
	server.server_run()