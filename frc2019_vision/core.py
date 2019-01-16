import cv2

from . import Target, enviorment, gui, vision


def set_camera(port: int):
    enviorment.VIDEO_STREAM = port

def start_loop():
    # keep looping
    while True:
        # grab the current frame
        frame = enviorment.VIDEO_STREAM.read()

        # if we are viewing a video and we did not grab a frame,
        # then we have reached the end of the video
        if frame is None:
            break

        frame, cnts = vision.contour(frame)

        if enviorment.TARGET == Target.TAPE:
            frame = vision.detect_tape(frame, cnts)
        elif enviorment.TARGET == Target.BALL:
            frame = vision.detect_ball(frame, cnts)

        if enviorment.GUI:
            gui.draw_crosshairs(frame)

            # show the frame to our screen
            cv2.imshow("Frame", frame)
            key = cv2.waitKey(1) & 0xFF

            # if the 'q' key is pressed, stop the loop
            if key == ord("q"):
                break
