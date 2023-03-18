# Create a socket server that listens on port 8000 and logs messages from clients
# to the console.

import socket

import database

import threading

import sys


database.init()

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to the port
server_address = ("127.0.0.1", 8000)
print('starting up on %s' % server_address[0])
sock.bind(server_address)

# Listen for incoming connections
sock.listen(10)


threads = []


def anonymous_action(data, connection: socket.socket):
    print("Received: " + data)
    data = data.lower().strip().split(" ")
    if not (data[0].isalpha()):
        return "400 Invalid command format"
    if data[0] == "login":
        # Check command
        if (len(data) != 3):
            return "400 Invalid command format"

        return database.login(data[1], data[2])
    elif data[0] == "quit":
        connection.send("200 OK".encode())
        connection.close()
        return None
    else:
        return "400 Invalid command", False, None


def process_data(data, connection: socket.socket, user, index):
    print("Received: " + data)
    data = data.lower().strip().split(" ")
    if not (data[0].isalpha()):
        return "400 Invalid command format"
    if data[0] == "buy":
        # Check command
        if (len(data) != 4):
            return "400 Invalid command format"

        return database.buy_stock(data[1].upper(), float(data[2]), float(data[3]), user[0])
    elif data[0] == "sell":
        # Check command
        if (len(data) != 4):
            return "400 Invalid command format"

        return database.sell_stock(data[1].upper(), float(data[2]), float(data[3]), user[0])
    elif data[0] == "list":
        return database.list_stocks(user) if not user[3] else database.list_stocks_root()
    elif data[0] == "balance":
        return database.get_balance(user[0])
    elif data[0] == "deposit":
        # Check command
        if (len(data) != 2):
            return "400 Invalid command format"

        return database.deposit(float(data[1]), user)
    elif data[0] == "who" and user[3]:
        result = "The list of active users:\n"
        for thread in threads:
            result += thread["user"] + "\t" + thread["address"] + "\n"

        return result.strip()
    elif data[0] == "lookup":
        # Check command
        if (len(data) != 2):
            return "400 Invalid command format"

        return database.lookup_stock(data[1], user)
    elif data[0] == "logout":
        connection.send("200 OK".encode())
        return None
    elif data[0] == "quit":
        connection.send("200 OK".encode())

        threads.pop(index)
        sys.exit()
    elif data[0] == "shutdown" and user[3]:
        connection.send("200 OK".encode())
        connection.close()
        sock.close()
        database.close()
        exit()
    else:
        return "400 Invalid command"


def thread_function(user, connection: socket.socket, index):
    while True:
        # receive data stream. it won't accept data packet greater than 1024 bytes
        data = connection.recv(1024).decode()
        if not data:
            # if data is not received break
            break

        message = process_data(data, connection, user, index)

        connection.send(str(message).encode())


while True:
    try:
        connection, address = sock.accept()  # accept new connection
        print("Connection from: " + str(address))

        # receive data stream. it won't accept data packet greater than 1024 bytes
        data = connection.recv(1024).decode()
        print("Received: " + data)
        # if not data:
        #     # if data is not received break
        #     break

        # For login and quit
        message, success, user = anonymous_action(data, connection)

        while not success:
            connection.send(str(message).encode())
            data = connection.recv(1024).decode()
            if not data:
                # if data is not received break
                break

            message, success, user = anonymous_action(data, connection)

        connection.send(str(message).encode())

        if success:
            # Create new thread
            threads.append({"user": user[0], "address": address[0], "thread": threading.Thread(
                target=thread_function, args=(user, connection, len(threads)))})
            threads[-1]["thread"].start()
    # If socket is closed we should exit
    except:
        exit()
