from .networking import (
    DriverstationConnectionFactoryThread,
    RioConnectionFactoryThread,
)
from .vision.vision import VisionThread


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
