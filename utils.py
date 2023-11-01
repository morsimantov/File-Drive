import socket
import sys
import os
import time

BUFFER_SIZE = 4096  # send 4096 bytes each time


def preform_updates(sending_socket, path, request, type_item):
    print("got here")
    if request == "delete":
        if type_item == "file" and os.path.isfile(path):
            os.remove(path)
        # if it's a directory, delete it and all of its files
        else:
            delete_dir(path)
    if request == "create":
        # create a new file
        if type_item == "file":
            print("inside 'create' request : ")
            # new_file_name = os.path.basename(os.path.normpath(path))
            print(path)
            copy_file(path, sending_socket)
            # copy_file(new_file_name,client_socket)
        # create a new directory at the server
        else:
            print(path, "created")
            copy_directory(path)
    # if there has been any change in the file/dir, replace them
    if request == "modify":
        if type_item == "file":
            print("inside 'modify' request")
            os.remove(path)
            copy_file(path)
        else:
            delete_dir(path)
            copy_directory(path)


# function that deletes all items in the folder recursively in order to delete a directory
def delete_dir(file_path):
    directory = os.path.abspath(file_path)
    for root, dirs, files in os.walk(directory, topdown=False):
        for name in dirs:
            print("dir: " + os.path.join(root, name))
            delete_dir(os.path.join(root, name))
        for name in files:
            print("file: " + os.path.join(root, name))
            os.remove(os.path.join(root, name))
    os.rmdir(directory)


def copy_directory(path):
    os.mkdir(path)


def copy_file(path, client_socket):
    print("hereee! " +path)
    #place = os.path.split(os.path.split(path)[0])[1]
    #os.chdir(os.getcwd().join(place))
    with open(path, "wb") as f:
        while True:
            # read 1024 bytes from the socket (receive)
            bytes_read = client_socket.recv(BUFFER_SIZE)
            if not bytes_read:
                # nothing is received
                # file transmitting is done
                break
            # write to the file the bytes we just received
            f.write(bytes_read)
    # close the client socket
    #client_socket.close()
    # close the server socket


def send_path(path, s):
    s.send(path.encode())


def send_file(file_path, s):  # the file path has the file that we want to send
    # file_size = os.path.getsize(file_path)  # the file size in bytes
    # s.send(f"{file_path}{SEPARATOR}{file_size}".encode())
    # SEPARATOR here just to separate the data fields
    # encode() encodes the string we passed to 'utf-8' encoding (that's necessary).

    # now we start the sending of the file:
    ''''
    Basically what we are doing here is opening the file as read in binary,
    read chunks from the file (in this case, 4096 bytes or 4KB)
    and send them to the socket using the sendall() function,
     once that's finished, we close that socket.
    '''
    # with open(file_path, encoding='utf-8') as f:
    file_name = os.path.basename(os.path.normpath(file_path))
    # with open(file_path, "rb") as f:
    with open(file_path, "rb") as f:
        if(os.path.isfile(file_path)):
            while True:
                # reads the bytes from the file:
                bytes_read = f.read(BUFFER_SIZE)
                if not bytes_read:
                    break  # means the file transition is finished
                # sendall is to assure transimission in busy networks
                # sendall is to send to the socket
                s.sendall(bytes_read)
        if(os.path.isdir(file_path)):
            print("it is a dir!")
    s.close()  # closing the socket todo check if needed
