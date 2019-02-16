import socket


try:
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    client.bind(("", 9999))
    while True:
        data, addr = client.recvfrom(65536)
        print("received message: " + str(data) + "\n")
        client.sendto(b"I am here", addr)
except KeyboardInterrupt:
    pass
