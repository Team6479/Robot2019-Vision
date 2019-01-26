from imutils.video import VideoStream

from . import OverwritingLifoQueue, Target


TARGET: OverwritingLifoQueue = OverwritingLifoQueue(2)
# Set default value of Target
TARGET.put(Target.NONE)

GUI: bool = False
CAMERA_PORT: int = 2
VIDEO_STREAM: VideoStream = VideoStream(src=CAMERA_PORT).start()

# Vision Information
DISTANCE_FROM_OBJECT: OverwritingLifoQueue = OverwritingLifoQueue(2)
ANGLE_FROM_CENTER: OverwritingLifoQueue = OverwritingLifoQueue(2)
