# Create a socket server that listens on port 8000 and logs messages from clients
# to the console.

import socket

import database

database.init()

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to the port
server_address = ("127.0.0.1", 8000)
print('starting up on %s' % server_address[0])
sock.bind(server_address)

# Listen for incoming connections
sock.listen(1)


connection, address = sock.accept()  # accept new connection
print("Connection from: " + str(address))


def process_data(data, connection: socket.socket):
    print("Received: " + data)
    data = data.lower().strip().split(" ")
    if not(data[0].isalpha()):
        return "400 Invalid command format"
    if data[0] == "buy":
        # Check command
        if (len(data) != 5):
            return "400 Invalid command format"

        return database.buy_stock(data[1].upper(), float(data[2]), float(data[3]), int(data[4]))
    elif data[0] == "sell":
        # Check command
        if (len(data) != 5):
            return "400 Invalid command format"

        return database.sell_stock(data[1].upper(), float(data[2]), float(data[3]), int(data[4]))
    elif data[0] == "list":
        return database.list_stocks(1)
    elif data[0] == "balance":
        return database.get_balance(1)
    elif data[0] == "quit":
        connection.send("200 OK".encode())
        connection.close()
        database.close()
        return None
    elif data[0] == "shutdown":
        connection.send("200 OK".encode())
        connection.close()
        sock.close()
        database.close()
        exit()
    else:
        return "400 Invalid command"


while True:

    # receive data stream. it won't accept data packet greater than 1024 bytes
    data = connection.recv(1024).decode()
    if not data:
        # if data is not received break
        break

    message = process_data(data, connection)

    if (message is None):
        connection, address = sock.accept()  # accept new connection
        continue

    # send data to the client
    connection.send(str(message).encode())

connection.close()
