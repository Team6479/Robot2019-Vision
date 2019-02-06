import pickle
import socket
import socketserver
import time
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
        # fmt: off
        self._ip = netifaces.ifaddresses(environment.NETIFACE)[netifaces.AF_INET][0]["addr"]  # noqa
        # fmt: on
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


class KeepAliveThread(StoppableThread):
    def __init__(self, request: socket.socket, stop_func):
        StoppableThread.__init__(self)
        self._request: socket.socket = request
        self._stop_func = stop_func

    def run(self):
        self._request.settimeout(1)

        while not self.stopped():
            if self.stopped():
                continue

            try:
                self._request.recv(1024)
            except socket.timeout:
                self._stop_func()
                self.stop()


class DriverstationConnectionHandler(socketserver.BaseRequestHandler):
    def __init__(self, request, client_address, server):
        self.request = request
        self.client_address = client_address
        self.server = server
        self._stopped = False
        self.setup()
        try:
            self.handle()
        finally:
            self.finish()

    def handle(self):
        # initial = self.request[0].strip()
        socket: socket.socket = self.request[1]

        keep_alive = KeepAliveThread(socket, self.stop)
        # keep_alive.start()

        packets = 0
        while not self._stopped:
            # print("CONNECTED: " + str(initial.decode('utf-8')))
            # somehow get feed
            feed = environment.DRIVERSTATION_FRAMES.get()
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 40]
            result, encimg = cv2.imencode(".jpg", feed, encode_param)
            packet = pickle.dumps([encimg, packets])
            # socket.sendto(packet, self.client_address)
            socket.sendto(packet, (self.client_address[0], 9999))
            packets = packets + 1

    def stop(self):
        self._stopped = True


class DriverstationConnectionFactoryThread(StoppableThread):
    def __init__(self):
        StoppableThread.__init__(self)
        # fmt: off
        self._HOST = netifaces.ifaddresses(environment.NETIFACE)[netifaces.AF_INET][0]["addr"] # noqa
        # fmt: on
        self._PORT = 9998
        self._server = socketserver.ThreadingUDPServer(
            (self._HOST, self._PORT), DriverstationConnectionHandler
        )

    def run(self):
        try:
            self._server.serve_forever()
        except Exception:
            self.stop()

    def stop(self):
        self._server.shutdown()


class DriverstationBroadcastThread(StoppableThread):
    def __init__(self):
        StoppableThread.__init__(self)
        # fmt: off
        self._broadcast = netifaces.ifaddresses(environment.NETIFACE)[netifaces.AF_INET][0]["broadcast"] # noqa
        # fmt: on
        self._send_port = 9999
        self._recv_port = 9998
        self._server = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP
        )

    def run(self):
        self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        # Set a timeout so the socket does not block
        # indefinitely when trying to receive data.
        self._server.settimeout(0)
        self._server.bind(("", self._recv_port))

        packets = 0
        PACKET_TIME_MS = 33
        prev_time = 0
        while not self.stopped():
            if self.stopped():
                continue

            current_time = int(time.time() * 1000)
            time_diff = abs(prev_time - current_time)
            if time_diff < PACKET_TIME_MS:
                # print("Sleeping for: " + str(time_diff / 1000))
                self._stop_event.wait(time_diff / 1000)
            prev_time = current_time

            feed = environment.DRIVERSTATION_FRAMES.get()
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 40]
            result, encimg = cv2.imencode(".jpg", feed, encode_param)
            packet = pickle.dumps([encimg, packets])
            self._server.sendto(packet, (self._broadcast, self._send_port))
            packets = packets + 1
