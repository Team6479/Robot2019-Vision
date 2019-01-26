from .networking import RioConnectionFactoryThread
from .vision.vision import VisionThread


VISION_THREAD = VisionThread()
RIO_THREAD = RioConnectionFactoryThread()


def start():
    VISION_THREAD.start()
    RIO_THREAD.start()


def stop():
    VISION_THREAD.stop()
    RIO_THREAD.stop()
