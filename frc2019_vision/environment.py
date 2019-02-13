from imutils.video import VideoStream

from . import OverwritingLifoQueue, Target

TARGET: OverwritingLifoQueue = OverwritingLifoQueue(2)
# Set default value of Target
TARGET.put(Target.NONE)

GUI: bool = False
CAMERA_PORT: int = 0
VideoStream = VideoStream(src=CAMERA_PORT).start()
VIDEO_STREAM: VIDEO_STREAM.set(cv2.CAP_PROP_EXPOSURE,-8)
 
# Vision Information
DISTANCE_FROM_OBJECT: OverwritingLifoQueue = OverwritingLifoQueue(2)
ANGLE_FROM_CENTER: OverwritingLifoQueue = OverwritingLifoQueue(2)
