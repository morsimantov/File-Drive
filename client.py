import socket
import sys
import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import utils


def main():
    # the identifier is optional, not always received
    global identifier
    global ip_address
    global server_port
    global update_seconds
    # get arguments from the user
    if len(sys.argv) == 5:
        ip_address = sys.argv[1]
        server_port = int(sys.argv[2])
        # path of the folder
        path_from_args = sys.argv[3]
        # fixed period of time for the server to treat the client
        update_seconds = sys.argv[4]
        identifier = ""
    if len(sys.argv) == 6:
        ip_address = sys.argv[1]
        server_port = int(sys.argv[2])
        path_from_args = sys.argv[3]
        update_seconds = sys.argv[4]
        # identifier of the client if it has a folder that's already saved on the server
        identifier = sys.argv[5]
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((ip_address, server_port))
    # create an observer
    global len_head
    global main_path
    file_name = os.path.basename(path_from_args)
    path = os.path.join(identifier, file_name)
    len_head = len(path_from_args) - len(file_name)
    main_path = path_from_args[:len_head]
    # if none then the client needs to look at the file as a new file that the server doesn't know
    if identifier == "":
        # the number -1 will represent a new file
        new_dir_id = "-1"
        # -1 in bytes
        bytes_val_new = new_dir_id.encode()
        # send the number '-1' in bytes to the server
        s.send(bytes_val_new)
        # the new identifier we get back from the server
        identifier = s.recv(128).decode()
        # send the directory to the server
        utils.send_path(path, s)
        time.sleep(5)
        send_directory_to_server(path_from_args, path, identifier, server_port, ip_address)
    # in case the client does receive an identifier
    else:
        if not os.path.exists(path_from_args):
            utils.copy_directory(path_from_args)
        message = "new"
        message_b = message.encode()
        identifier_b = identifier.encode()
        folder_name = os.path.basename(path_from_args)
        folder_name_b = folder_name.encode()
        # sending  the identifier in bytes
        s.send(identifier_b + message_b + folder_name_b)
        receive_directory_from_client(s, path_from_args, file_name)
    go_recursively = True
    observer = Observer()
    observer.schedule(file_event_handler, path_from_args, recursive=go_recursively)
    # start the observer
    observer.start()
    while True:
        time.sleep(5)
    s.close()


# help function that formats the information needed to handle the event
def request_event_id_formatted(request, event):
    event_path = event.src_path[len_head:]
    return request.encode(), event_path, identifier.encode()


# when a directory\file created
def on_created(event):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((ip_address, server_port))
    request_type, event_path, identifier_in_bytes = request_event_id_formatted('create', event)
    if event.is_directory:
        # request in bytes
        created_type = 'dire'.encode()
        time.sleep(5)
        # send the message to the server
        s.send(identifier_in_bytes + request_type + created_type)
        # send the path to the server
        utils.send_path(event_path, s)
    else:
        created_type = 'file'.encode()
        time.sleep(5)
        s.send(identifier_in_bytes + request_type + created_type)
        # send the path to the server
        utils.send_path(event_path, s)
        # send the file itself to the server
        utils.send_file(event.src_path, s)
    s.close()


# when a directory\file deleted
def on_deleted(event):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((ip_address, server_port))
    time.sleep(3)
    request_type, event_path, identifier_in_bytes = request_event_id_formatted('delete', event)
    if event.is_directory and event.src_path.isdir():
        # request in bytes
        created_type = 'dire'.encode()
        s.send(identifier_in_bytes + request_type + created_type)
        # send the path of the directory to delete
        utils.send_path(event_path, s)
    else:
        created_type = 'file'.encode()
        s.send(identifier_in_bytes + request_type + created_type)
        # send the path of the file to delete
        utils.send_path(event_path, s)
    s.close()


# tried to take care of changing file's contents in modified, didn't work (didn't have time)
def on_modified(event):
    if event.is_directory:
        return
    # request_type_first = 'delete'.encode()
    # request_type_second = 'create'.encode()
    # event_src_path = event.src_path[len_head:]
    # print(event_src_path)
    # identifier_in_bytes = identifier.encode()  # id in bytes
    # if not event.is_directory:
    #     s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #     s.connect((ip_address, server_port))
    #     created_type = 'file'.encode()
    #     s.send(identifier_in_bytes + request_type_first + created_type)
    #     time.sleep(3)
    #     utils.send_path(event_src_path, s)
    #     s.close()
    #     time.sleep(5)
    #     s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #     s.connect((ip_address, server_port))
    #     s.send(identifier_in_bytes + request_type_second + created_type)  # create
    #     time.sleep(5)
    #     utils.send_path(event_src_path, s)  # the path to create
    #     utils.send_file(event.src_path, s)
    #     s.close()


# when the directory\file moved or the name of the directory\file changed
def on_moved(event):
    request_type_first = 'delete'.encode()
    request_type_second = 'create'.encode()
    event_src_path = event.src_path[len_head:]
    event_dest_path = event.dest_path[len_head:]
    identifier_in_bytes = identifier.encode()
    if event.is_directory:
        # if the basename of the source path and the destination path is the same
        if os.path.basename(event.dest_path) == os.path.basename(event.src_path):
            return
        else:
            # delete the directory
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((ip_address, server_port))
            # request in bytes
            created_type = 'dire'.encode()
            s.send(identifier_in_bytes + request_type_first + created_type)
            time.sleep(3)
            # send the path to delete
            utils.send_path(event_src_path, s)
            s.close()
            time.sleep(5)
            event_dest_path_full = event.dest_path
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((ip_address, server_port))
            s.send(identifier_in_bytes + request_type_second + created_type)
            time.sleep(5)
            # send the path to create
            utils.send_path(event_dest_path, s)
            s.close()
            # create the directories recursively (if there is more than one)
            send_directory_to_server(event_dest_path_full, event_dest_path, identifier, server_port, ip_address)
    else:
        # delete the file
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip_address, server_port))
        created_type = 'file'.encode()
        s.send(identifier_in_bytes + request_type_first + created_type)
        time.sleep(3)
        utils.send_path(event_src_path, s)
        s.close()
        time.sleep(5)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip_address, server_port))
        s.send(identifier_in_bytes + request_type_second + created_type)
        time.sleep(5)
        # send the path to create
        utils.send_path(event_dest_path, s)
        # send the file itself
        utils.send_file(event.dest_path, s)
        s.close()
    s.close()


# function that sends the data in a directory recursively from client to server
def send_directory_to_server(path, folder, identifier, server_port,ip_address):
    request = "create"
    request_type = request.encode()
    identifier_in_bytes = identifier.encode()
    for root, dirs, files in os.walk(path, topdown=True):
        relative_path = root.replace(path, folder)
        for name in files:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((ip_address, server_port))
            created_type = 'file'.encode()
            time.sleep(5)
            path_to_send = os.path.join(relative_path, name)
            s.send(identifier_in_bytes + request_type + created_type)
            utils.send_path(path_to_send, s)
            utils.send_file(os.path.join(root, name), s)
            s.close()
        for name in dirs:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((ip_address, server_port))
            created_type = 'dire'.encode()
            time.sleep(5)
            s.send(identifier_in_bytes + request_type + created_type)
            path_to_send = os.path.join(relative_path, name)
            utils.send_path(path_to_send, s)
            s.close()


# function that receives a directory from the client
def receive_directory_from_client(s, client_path, folder):
    data = s.recv(1024)
    while data:
        request = (data[:6]).decode('utf-8')
        # if there is a new change
        # type can be "file" or "dire" (directory)
        type_item = (data[6:10]).decode('utf-8')
        # receive the file info's
        received = s.recv(BUFFER_SIZE)
        parted_path = received.decode()
        length = len(client_path) - len(folder) - 1
        client_path_head = client_path[:length]
        # create a new path of the server and the path received combined
        path = os.path.join(client_path_head, parted_path)
        utils.preform_updates(s, path, request, type_item)
        data = s.recv(1024)
    s.close()


# function that updates the changes that the server sent
def changes_from_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((ip_address, server_port))
    identifier_b = identifier.encode()
    request = "checks"
    request_b = request.encode()
    s.send(identifier_b + request_b)
    received = s.recv(1024)
    s.close()
    request = received[:7].decode()
    if request == "none! ":
        return
    type_item = received[7:11].decode()
    path = received[11:].decode()
    path = os.path.join(main_path, path)
    utils.preform_updates(s, path, request, type_item)


if __name__ == '__main__':
    # send 4096 bytes each time
    BUFFER_SIZE = 4096
    SEPARATOR = "<SEPARATOR>"
    patterns = ["*"]
    ignore_patterns = None
    ignore_directories = False
    case_sensitive = True
    file_event_handler = FileSystemEventHandler()
    file_event_handler.on_created = on_created
    file_event_handler.on_deleted = on_deleted
    file_event_handler.on_modified = on_modified
    file_event_handler.on_moved = on_moved
    main()
