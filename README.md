# File-Drive

## About

We created a cloud service that allows backup of files for clients, like a file drive.

We implemented a client and a TCP-server to do so.

The client can choose a folder on his computer and synchronize it automatically across different computers.

When the program is activated and receives a folder to backup, it backs it up on the server and for now on monitors any change within the folder and its files deeply (i.e. in sub-folders and files).
Now when the server recognizes any change as such, the program updates all the computers of the client that have the same folder.

The server knows to handle several clients a-synchronically, it handles a single client each time.

Every new client receives a unique Id number. The client keeps the Id number and in any future contact he must identify with this number. 

## Compiling and Running

You must have Python 3.10 or higher installed. Run the server.py by the following command in the terminal:

python3 server.py X

Where X represents the port number the server is listening to - choose any number from 1 to 2^16^-1.

Than run the client.py file by the following command :

python3 client.py Y X _name folder 10

The parameters by order: Y = server's IP address, X = server's port number, the folder you want to backup and period of time (in seconds) for the client to be treated by the server.
