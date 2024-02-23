# COMP3234 -  Instant Messaging App

## Startup

The client consists of two parts, the client and server program.

To run the server program use the following command

`python3 server.py <server port> <password file path>`

To run the client server use the following command

`python3 client.py <server_Port> <server_IP>`

Note that the the client server may refuse to run if the server is not already running.

**Example**

Server running on port 8000 of user's machine using the provided file path as the location of the passwords

`python server.py 8000 ./.passwords/usernameAndPasswords.txt`

Client running on the same machine as ther server, connecting to the server on port 8000

`python client.py "" 8000`

## Features

The server program implements some additional features.

First, in this implementation we do not allow multiple logins from the same user. To test this feature you can login first with some user registered in the system and then open a new commandline to attempt login with the same credentials.

Further, a client cannot send messages to themselves.

Additionally a client may use any of the following to logoff or exit the session:

`"/exit"` or `"exit"` or `"quit"` or `"logout"` or `"logoff"` or `"bye"`

The programs are reasonably robust. Client programs after abruptly ending are logged out by the server. If a user wishes to shut down the server using a keyboard interrupt then the server will first attempt to logoff all online users and then quit. In case the server crashes, the clients only learn about it when they attempt to interact with it at which stage the client is informed of the server's status and is logged out (i.e. client program exits).

## Implementation Specific Details

The server uses code 103 to communicate to the client that it already has an open session with the same username.

The sockets used for the initial connection created between the server and client is called socket A while the other channel is called socket B

We use `__new__()` method for object creation in an unconventional manner to return the socket port number (alongside the thread object) upon creation of the new client thread in `client.py`

We use a 2 second timeout on the server threads handling clients that upon timeout checks it has been marked for cleanup using the `forceQuit` boolean flag.

## Known Issues

If a user is already typing a message and recieves a message while text has been fed to the terminal it may be overwritten visually by the incoming text but still remains intact (just not visible to the user).  Fixing this bug is trivial with a GUI so I did not spend time solving it in a CLI.
