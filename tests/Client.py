"""A simple TCP client made to test making requests"""

import socket
import sys

HOST, PORT = "localhost", 5005

# Create a socket (SOCK_STREAM means a TCP socket)
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    try:
        # Connect to server and send data
        sock.connect((HOST, PORT))
        while True:
            data = input("String: ")
            sock.sendall(bytes(data + "\n", "utf-8"))

            # Receive data from the server and shut down
            received = str(sock.recv(1024), "utf-8")

            print("Sent:     {}".format(data))
            print("Received: {}".format(received))
    except KeyboardInterrupt:
        sys.exit()
