# Create a socket server that listens on port 8000 and logs messages from clients
# to the console.

import socket

import database

import threading

import sys

import select


database.init()

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to the port
server_address = ("127.0.0.1", 8000)
print('starting up on %s' % server_address[0])
sock.bind(server_address)

# Listen for incoming connections
sock.listen(10)

socks = [sock]


threads = []

shutdown_requested = False


def anonymous_action(data, connection: socket.socket):
    print("Received: " + data)
    data = data.lower().strip().split(" ")
    if not (data[0].isalpha()):
        return "400 Invalid command format", False, None, False
    if data[0] == "login":
        # Check command
        if (len(data) != 3):
            return "400 Invalid command format", False, None, False

        return database.login(data[1], data[2])
    elif data[0] == "quit":
        if (len(data) != 1):
            return "400 Invalid command format", False, None, False
        connection.send("200 OK".encode())
        return None, False, None, False
    else:
        return "400 Invalid command", False, None, False


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
        # Check command
        if (len(data) != 1):
            return "400 Invalid command format"

        return database.get_balance(user[0])
    elif data[0] == "deposit":
        # Check command
        if (len(data) != 2) or not data[1].isdigit():
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
        threads.pop(index)
        return None
    elif data[0] == "quit":
        # Check command
        if (len(data) != 1):
            return "400 Invalid command format"

        connection.send("200 OK".encode())
        threads.pop(index)
        sys.exit()
    elif data[0] == "shutdown" and user[3]:
        global shutdown_requested
        shutdown_requested = True
        global socks

        connection.send("200 OK".encode())
        for s in socks:
            try:
                s.close()
            except:
                pass
        sock.close()

        database.close()
        return None, True  # true value is shutdown flag
    else:
        return "400 Invalid command"


def thread_function(user, connection: socket.socket, index):
    while True:
        try:
            data = connection.recv(1024).decode()
            if not data:
                # if data is not received break
                break

            message = process_data(data, connection, user, index)
            # For logout
            if message is None:
                # Exit thread
                return

            try:
                connection.send(str(message).encode())
            except OSError as e:
                # after shutdown os will try to send a message on closed socket
                # this catches it
                break
        except:
            break
    connection.close()


while True:
    try:
        if shutdown_requested:
            break
        socks = [s for s in socks if s.fileno() != -1]
        readable, writable, exceptionavailable = select.select(socks, [], [])
        for s in readable:
            if shutdown_requested:
                break
            if (s == sock):
                connection, address = sock.accept()
                socks.append(connection)
                print("Connection from: " + str(address))
            else:
                try:
                    # receive data stream. it won't accept data packet greater than 1024 bytes
                    try:
                        data = s.recv(1024).decode()
                    except OSError as e:
                        socks.remove(s)
                        s.close()
                        continue

                    # For login and quit
                    message, success, user, shutdown = anonymous_action(
                        data, s)

                    if shutdown:
                        socks.remove(s)
                        s.close()
                        break

                    if message is not None:
                        s.send(str(message).encode())

                    if success:
                        # Create new thread
                        threads.append({"user": user[0], "address": address[0], "thread": threading.Thread(
                            target=thread_function, args=(user, s, len(threads)))})
                        threads[-1]["thread"].start()
                    elif message is None:
                        # If the message is None, it means the client has sent a "quit" command
                        # So, we need to remove the connection from the socks list and close it
                        socks.remove(s)
                        s.close()
                except ConnectionAbortedError:
                    socks.remove(s)
                    s.close()
    except WindowsError:

        exit()
