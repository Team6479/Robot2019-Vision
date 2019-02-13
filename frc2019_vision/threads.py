from .networking import (
    DriverstationConnectionFactoryThread,
    RioConnectionFactoryThread,
)
from .vision.vision import VisionThread


VISION_THREAD = None
RIO_THREAD = None
DRIVERSTATION_THREAD = None


def create():
    global VISION_THREAD
    global RIO_THREAD
    global DRIVERSTATION_THREAD

    VISION_THREAD = VisionThread()
    RIO_THREAD = RioConnectionFactoryThread()
    DRIVERSTATION_THREAD = DriverstationConnectionFactoryThread()


def start():
    VISION_THREAD.start()
    RIO_THREAD.start()
    DRIVERSTATION_THREAD.start()


def stop():
    VISION_THREAD.stop()
    RIO_THREAD.stop()
    DRIVERSTATION_THREAD.stop()
