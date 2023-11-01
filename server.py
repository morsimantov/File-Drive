import socket
import sys
import random
import string
import os
import utils
import time


def main():
    port = int(sys.argv[1])
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('', port))
    dict_clients = {}
    server.listen()
    while True:
        client_socket, client_address = server.accept()
        client_ip_address, socket_number = client_address
        print(client_ip_address)
        # receive the data from client
        data = client_socket.recv(1024)
        # extract the id number of the client
        client_id = (data[:128]).decode('utf-8')
        # if the client is new and isn't backed up at the server yet
        if client_id == "-1":
            new_client(client_socket, dict_clients, client_ip_address)
        elif data[128:131].decode() == "new":
            folder_name = data[131:].decode()
            path_client = os.path.join(SERVER_PATH, client_id)
            path = os.path.join(path_client, folder_name)
            send_directory_to_client(path, folder_name, client_id, client_socket)
        # if the client is already in the dictionary, update the data at all the sockets (users)
        else:
            # save the request from the client. request can be: delete, create, change, moved, checks
            request = (data[128:134]).decode('utf-8')
            print("request: " + request)
            # if the client connects only to seek for changes
            if request == "checks":
                check_for_changes(client_id, client_socket, dict_clients, client_ip_address)
            # if there is a new change
            else:
                # type can be "file" or "dire" (directory)
                type_item = (data[134:]).decode('utf-8')
                # receive the file info's
                received = client_socket.recv(BUFFER_SIZE)
                # todo replace this with the path
                parted_path = received.decode()
                # print(path)
                # remove absolute path if there is
                # convert to integer
                # create a new path of the server and the path received combined
                print("parted path: " + parted_path)
                path_client = os.path.join(SERVER_PATH, client_id)
                path = os.path.join(path_client, parted_path)
                print(request + ": " + path)
                # save file path from the specific directory
                # file_path = file_path[file_path.index(file_name) + len(file_path):]
                existing_client(client_socket, client_id, path, request, type_item, dict_clients, parted_path, client_ip_address)
        client_socket.close()
        print('Client disconnected')


# inform the client about previous changes
def check_for_changes(client_id, client_socket, dict_clients, client_address):
    # check for any changes according to the id and the current client's ip
    # if the dict of updates by this ip dress is not empty
    print(dict_clients)
    print(client_id)
    if dict_clients[client_id][client_address] is None:
        print("there are no changes for " + client_address)
        return
    if dict_clients[client_id][client_address]:
        for change in dict_clients[client_id][client_address]:
            # if there is a change, send it to the current client
            request = change[0]
            type_item = change[1]
            path = change[2]
            client_socket.send(request.encode() + type_item.encode() + path.encode())
    else:
        message = "none! "
        client_socket.send(message.encode())


def new_client(client_socket, dict_clients, client_address):
    # when a new client wants to sign in at the server, send a random id number for the client
    client_id = ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=128))
    id_number_b = client_id.encode()
    # save the new client in the dictionary
    dict_clients[client_id] = {}
    dict_clients[client_id][client_address] = None
    client_socket.send(id_number_b)
    print(client_id)
    path_client = os.path.join(SERVER_PATH, client_id)
    os.mkdir(path_client)
    received = client_socket.recv(1024)
    path = received.decode()
    path = os.path.join(path_client, path)
    utils.copy_directory(path)


def existing_client(client_socket, client_id, path, request, type_item, dict_clients, parted_path, client_address):
    utils.preform_updates(client_socket, path, request, type_item)
    # save the new change in every ip of the client's id
    # toDo: what to save as the change
    # if the dictionary of client ids not empty, meaning there are other ips to update
    if not dict_clients:
        return
    if not dict_clients[client_id]:
        return
    for ip_address in dict_clients[client_id]:
        if ip_address != client_address:
            print("ip: " + ip_address)
            change = []
            change.append(request)
            change.append(type_item)
            change.append(parted_path)
            dict_clients[client_id][ip_address] = change
    # save the client in the dictionary
    # if there were previous changes for the same socket, inform the client about the changes
    # check_for_changes(client_id, client_socket, dict_clients, client_address)


# if the client is connection with an existing id
def send_directory_to_client(path, folder, identifier, client_socket):
    print("got path: " + path)
    print(folder)
    request = "create"
    request_type = request.encode()
    identifier_in_bytes = identifier.encode()
    for root, dirs, files in os.walk(path, topdown=True):
        relative_path = root.replace(path, folder)
        print("relative path: " + relative_path)
        for name in files:
            created_type = 'file'.encode()
            time.sleep(5)
            path_to_send = os.path.join(relative_path, name)
            client_socket.send(request_type + created_type)
            print("file: " + os.path.join(root, name))
            utils.send_path(path_to_send, client_socket)
            utils.send_file(os.path.join(root, name), client_socket)
        for name in dirs:
            created_type = 'dire'.encode()  # request in bytes
            time.sleep(5)
            client_socket.send(request_type + created_type)
            path_to_send = os.path.join(relative_path, name)
            print("dir: " + path_to_send)
            utils.send_path(path_to_send, client_socket)


if __name__ == '__main__':
    SERVER_PATH = os.path.dirname(os.path.abspath(__file__))
    BUFFER_SIZE = 4096  # send 4096 bytes each time
    SEPARATOR = "<SEPARATOR>"
    main()