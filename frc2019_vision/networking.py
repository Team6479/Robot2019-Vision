import pickle
import socketserver
from enum import Enum

import cv2

import netifaces

from . import StoppableThread, environment
from .events import handler as event_handler


class ConnectionType(Enum):
    TCP = 0
    UDP = 1


class RioConnectionHandler(socketserver.BaseRequestHandler):
    def handle(self):
        BUFFER_SIZE: int = 1024
        while True:
            # receive data
            raw_data = self.request.recv(BUFFER_SIZE)

            # if we receive an empty string assume the connection has closed
            # and break out of the while loop
            if raw_data == bytes("", "utf-8"):
                break

            # decode data
            decoded_data = raw_data.decode("utf-8")

            print("Received: " + decoded_data)
            # parses get or set
            reply: str = event_handler.parse(decoded_data.rstrip("\n").split(" "))
            self.request.send(bytes(reply, "utf-8"))
            print("Sent: " + reply)


class RioConnectionFactoryThread(StoppableThread):
    def __init__(self):
        StoppableThread.__init__(self)
        # self._ip = netifaces.ifaddresses("lo")[netifaces.AF_INET][0]["addr"]
        self._ip = netifaces.ifaddresses("eth0")[netifaces.AF_INET][0]["addr"]
        self._port = 5005
        self._server = socketserver.TCPServer(
            (self._ip, self._port), RioConnectionHandler
        )

    def run(self):
        try:
            self._server.serve_forever()
        except Exception:
            self.stop()

    def stop(self):
        self._server.shutdown()


class DriverstationConnectionHandler(socketserver.BaseRequestHandler):
    def handle(self):
        # initial = self.request[0].strip()
        socket = self.request[1]
        packets = 0
        while True:
            # print("CONNECTED: " + str(initial.decode('utf-8')))
            # somehow get feed
            feed = environment.DRIVERSTATION_FRAMES.get()
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 40]
            result, encimg = cv2.imencode(".jpg", feed, encode_param)
            packet = pickle.dumps([encimg, packets])
            socket.sendto(packet, self.client_address)
            packets = packets + 1


class DriverstationConnectionFactoryThread(StoppableThread):
    def __init__(self):
        self._HOST = netifaces.ifaddresses("eth0")[netifaces.AF_INET][0]["addr"]
        self._PORT = 9999
        self._server = socketserver.UDPServer(
            (self._HOST, self._PORT), DriverstationConnectionHandler()
        )

    def run(self):
        try:
            self._server.serve_forever()
        except Exception:
            self.stop()

    def stop(self):
        self._server.shutdown()
