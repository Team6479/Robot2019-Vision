import math

import cv2
import imutils

from . import Target, enviorment

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
BALL_RADIUS = 6.5
CAMERA_ANGLE = 60
ARCTAN_30 = 1.537

def create_windows():
    cv2.namedWindow("Frame", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Frame", SCREEN_WIDTH, SCREEN_HEIGHT)

    cv2.namedWindow("DBG", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("DBG", SCREEN_WIDTH, SCREEN_HEIGHT)

def contour(frame):
    if enviorment.TARGET == Target.TAPE:
        hsv_lower = (74, 28, 248)
        hsv_upper = (99, 74, 255)
    elif enviorment.TARGET == Target.BALL:
        hsv_lower = (0, 150, 148)
        hsv_upper = (15, 255, 255)
    else:
        hsv_lower = (0, 0, 0)
        hsv_upper = (0, 0, 0)

    # resize the frame, blur it, and convert it to the HSV
    # color space
    frame = imutils.resize(frame, width=800)
    blurred = cv2.GaussianBlur(frame, (11, 11), 0)
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

    # construct a mask for the color "green", then perform
    # a series of dilations and erosions to remove any small
    # blobs left in the mask
    mask = cv2.inRange(hsv, hsv_lower, hsv_upper)
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
    if cnts:
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
    if cnts:
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
