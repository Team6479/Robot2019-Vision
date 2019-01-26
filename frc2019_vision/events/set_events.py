from imutils.video import VideoStream

from . import assemble_message
from .. import Target, args, environment
from .base_events import BaseSetEvent


class SetTarget(BaseSetEvent):
    @staticmethod
    def event_id() -> str:
        return "target"

    @staticmethod
    def run(arg: str) -> str:
        target = args.target(arg)
        if target == Target.NONE:
            return assemble_message("Invalid target", True)
        else:
            environment.TARGET.put(target)
            return assemble_message("Target set to: {}".format(target.value))


class SetCameraPort(BaseSetEvent):
    @staticmethod
    def event_id() -> str:
        return "cameraport"

    @staticmethod
    def run(arg: str) -> str:
        environment.CAMERA_PORT = arg
        environment.VIDEO_STREAM = VideoStream(src=environment.CAMERA_PORT).start()
