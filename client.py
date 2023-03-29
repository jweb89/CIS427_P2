# Create a client that can send messages to the server and receive replies running on port 8000 from the server in server.py

import socket
import sys
# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


# Get the IP address from command line arguments
if len(sys.argv) != 2:
    print("Usage: python client.py <IP address>")
    sys.exit(1)

# Connect the socket to the port where the server is listening
IP_ADDRESS = sys.argv[1]
server_address = (IP_ADDRESS, 8000)


print('connecting to %s' % server_address[0])
sock.connect(server_address)

logged_in_as_root = False  

try:

  

    message = ""
    while (True):
        try:
            message = input(" -> ")  # take input
            if message.lower().strip() == 'login root root01':
                logged_in_as_root = True
            if message.lower().strip() == 'logout':
                logged_in_as_root = False
             #space will be added to messasge when not root
             #this causes the command to be invalid and also not trigger 
             #the loop break for shutdown intended for only root users
            if message.lower().strip() == 'shutdown' and not logged_in_as_root:
                message="shutdown "
                

            sock.send(message.encode())  # send message
            data = sock.recv(1024).decode()  # receive response

            if not data:
                # if data is not received break
                break

            print(data)  # show in terminal
            if message.lower().strip() in ['quit']:
                break
            if message.lower().strip() in ['shutdown'] and logged_in_as_root:
                break
          

        except:
            break


finally:
    print('closing socket')