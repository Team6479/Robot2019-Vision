from imutils.video import VideoStream

from . import Target


TARGET: Target = Target.NONE

GUI: bool = False
CAMERA_PORT: int = 2
VIDEO_STREAM: VideoStream = VideoStream(src=CAMERA_PORT).start()
