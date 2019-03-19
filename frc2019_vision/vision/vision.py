import cv2
import imutils

from . import constants, gui, pipeline
from .. import StoppableThread, Target, environment


def update_enviornment(distance, angle):
    # Update values in the enviorment
    environment.DISTANCE_FROM_OBJECT.put(distance)
    environment.ANGLE_FROM_CENTER.put(angle)


def create_windows():
    cv2.namedWindow("Frame", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Frame", constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT)


class VisionThread(StoppableThread):
    def __init__(self):
        StoppableThread.__init__(self)

    def run(self):
        try:
            if environment.GUI:
                create_windows()

            while not self.stopped():
                if self.stopped():
                    continue
                # grab the current frame
                ret, frame = environment.VIDEO_STREAM.read()

                # if we are viewing a video and we did not grab a frame,
                # then we have reached the end of the video
                if not ret:
                    continue

                # frame = cv2.rotate(frame, rotateCode=cv2.ROTATE_90_COUNTERCLOCKWISE)

                # Put current frame (with crosshairs) in queue for Driverstation stream
                stream_frame = frame.copy()
                # stream_frame = imutils.resize(stream_frame, width=constants.SCREEN_WIDTH, height=constants.SCREEN_HEIGHT)
                # gui.draw_crosshairs(stream_frame)
                environment.DRIVERSTATION_FRAMES.put(stream_frame)

                target: Target = environment.TARGET.get()

                if target == Target.TAPE:
                    tape_pipeline = pipeline.TapePipeline(
                        calib_fname=constants.CALIBRATION_FILE_LOCATION
                    )
                    frame, dist, angle = tape_pipeline.process_image(frame)
                    update_enviornment(dist, angle)

                elif target == Target.BALL:
                    ball_pipeline = pipeline.BallPipeline()
                    frame, dist, angle = ball_pipeline.ball_val(frame)
                    update_enviornment(dist, angle)

                if environment.GUI:
                    gui.draw_crosshairs(frame)

                    # show the frame to our screen
                    gui.imshow("Frame", frame)
                    key = cv2.waitKey(1) & 0xFF

        except KeyboardInterrupt:
            self.stop()

    def stop():
        # When we break out of the while loop aka time to stop
        # we perform appropriate actions.
        # stop the camera video stream
        environment.VIDEO_STREAM.release()

        if environment.GUI:
            # close all windows
            cv2.destroyAllWindows()

        super().stop()
