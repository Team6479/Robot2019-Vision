import argparse
import math
import time
from collections import deque

import cv2
import imutils
import numpy as np
from imutils.video import VideoStream

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
BALL_RADIUS = 6.5
CAMERA_ANGLE = 60
ARCTAN_30 = 1.537

ap = argparse.ArgumentParser()
ap.add_argument("-t", "--target", type=str, default="ball", help="object to detect")
args = vars(ap.parse_args())


# define the lower and upper boundaries of the "green"
# ball in the HSV color space, then initialize the
# list of tracked points
# colorLower = (5, 50, 50)

if args["target"] == "tape":
    HSV_LOWER = (74, 28, 248)
    HSV_UPPER = (99, 74, 255)
elif args["target"] == "ball":
    HSV_LOWER = (0, 150, 148)
    HSV_UPPER = (15, 255, 255)

# if a video path was not supplied, grab the reference
# to the webcam
# VIDEO_STREAM = VideoStream(src=2).start()
VIDEO_STREAM = VideoStream(src=2).start()
VIDEO_STREAM.stream.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
# VIDEO_STREAM.set(cv2.CAP_PROP_EXPOSURE, -10)

# allow the camera or video file to warm up

cv2.namedWindow("Frame", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Frame", SCREEN_WIDTH, SCREEN_HEIGHT)

cv2.namedWindow("DBG", cv2.WINDOW_NORMAL)
cv2.resizeWindow("DBG", SCREEN_WIDTH, SCREEN_HEIGHT)

def contour(frame):
    # resize the frame, blur it, and convert it to the HSV
    # color space
    frame = imutils.resize(frame, width=800)
    blurred = cv2.GaussianBlur(frame, (11, 11), 0)
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

    # construct a mask for the color "green", then perform
    # a series of dilations and erosions to remove any small
    # blobs left in the mask
    mask = cv2.inRange(hsv, HSV_LOWER, HSV_UPPER)
    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)
    cv2.imshow("DBG", mask)
    # find contours in the mask and initialize the current
    # (x, y) center of the ball
    cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)

    return frame, cnts

def detect_ball(frame, cnts):
    center = None

    # only proceed if at least one contour was found
    if len(cnts) > 0:
        # find the largest contour in the mask, then use
        # it to compute the minimum enclosing circle and
        # centroid

        c = max(cnts, key=cv2.contourArea)
        ((x, y), radius) = cv2.minEnclosingCircle(c)
        M = cv2.moments(c)
        center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

        # only proceed if the radius meets a minimum size
        if radius > 10:
            # draw the circle and centroid on the frame,
            # then update the list of tracked points
            cv2.circle(frame, (int(x), int(y)), int(radius), (0, 255, 255), 2)
            cv2.circle(frame, center, 5, (0, 0, 255), -1)

        rpixel = radius
        ypixel = SCREEN_WIDTH / 2
        yinch = (ypixel * BALL_RADIUS) / rpixel
        calibration = 1.5
        xinch = (yinch * ARCTAN_30) * calibration

        centerx = x
        dpixel = centerx - 400
        dinch = (dpixel * BALL_RADIUS) / rpixel
        alpha = (math.atan(dinch / xinch)) * 57.296

        cv2.putText(
            frame,
            str(int(radius)) + " " + str(len(cnts)),
            (5, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 0, 0),
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            frame,
            "Distance (Inches): " + str(int(xinch)),
            (5, 55),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 0, 0),
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            frame,
            "Angle (Degrees): " + str(int(alpha)),
            (5, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 0, 0),
            2,
            cv2.LINE_AA,
        )

    return frame

def detect_tape(frame, cnts):
    center = None

    # only proceed if at least one contour was found
    if len(cnts) > 0:
        # find the largest contour in the mask, then use
        # it to compute the minimum enclosing circle and
        # centroid

        c = max(cnts, key=cv2.contourArea)
        ((x, y), radius) = cv2.minEnclosingCircle(c)
        M = cv2.moments(c)
        center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

        # only proceed if the radius meets a minimum size
        if radius > 5:
            # draw the circle and centroid on the frame,
            # then update the list of tracked points
            # cv2.circle(frame, (int(x), int(y)), int(radius), (0, 255, 255), 2)
            # cv2.circle(frame, center, 5, (0, 0, 255), -1)
            x1 = x - (radius / 2.75)
            y1 = y + radius
            x2 = x + (radius / 2.75)
            y2 = y - radius
            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (255, 0, 0), 2)
            cv2.circle(frame, center, 5, (0, 0, 255), -1)
    return frame


# keep looping
while True:
    # grab the current frame
    frame = VIDEO_STREAM.read()

    # if we are viewing a video and we did not grab a frame,
    # then we have reached the end of the video
    if frame is None:
        break

    frame, cnts = contour(frame)

    if args["target"] == "tape":
        frame = detect_tape(frame, cnts)
    elif args["target"] == "ball":
        frame = detect_ball(frame, cnts)

    # Draw main vertical line
    cv2.line(frame, (400, 0), (400, 600), (0, 0, 255), 2)
    # Draw main horizontal line
    cv2.line(frame, (0, 300), (800, 300), (0, 0, 255), 2)

    # Draw two guide lines
    cv2.line(frame, (350, 100), (350, 500), (0, 0, 255), 2)
    cv2.line(frame, (450, 100), (450, 500), (0, 0, 255), 2)

    # show the frame to our screen
    cv2.imshow("Frame", frame)
    key = cv2.waitKey(1) & 0xFF

    # if the 'q' key is pressed, stop the loop
    if key == ord("q"):
        break

# if we are not using a video file, stop the camera video stream
VIDEO_STREAM.stop()

# close all windows
cv2.destroyAllWindows()
