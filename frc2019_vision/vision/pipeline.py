import collections
import math
import os
import pickle
from typing import List, Optional, Tuple

import cv2
import imutils
import numpy as np

from . import constants

CalibrationResults = collections.namedtuple(
    "CalibrationResults", ["camera_matrix", "dist_coeffs", "rvecs", "tvecs", "fisheye"]
)
CalibrationResults.__new__.__defaults__ = (False,)

lower_green = np.array([0, 220, 25])
upper_green = np.array([101, 255, 255])

lower_orange = np.array([3, 119, 138])
upper_orange = np.array([31, 255, 255])


class BallPipeline:
    def contour(self, frame):
        # resize the frame, blur it, and convert it to the HSV
        # color space
        frame = imutils.resize(frame, width=800)
        blurred = cv2.blur(frame, (27, 27))
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

        # construct a mask for the color "green", then perform
        # a series of dilations and erosions to remove any small
        # blobs left in the mask
        mask = cv2.inRange(hsv, lower_orange, upper_orange)
        # find contours in the mask and initialize the current
        # (x, y) center of the ball
        cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)

        return frame, cnts

    def detect_ball(self, frame, cnts):
        center = None

        # only proceed if at least one contour was found
        if cnts:
            # find the largest contour in the mask, then use
            # it to compute the minimum enclosing circle and
            # centroid

            c = max(cnts, key=cv2.contourArea)
            ((x, y), radius) = cv2.minEnclosingCircle(c)
            M = cv2.moments(c)
            center = (0, 0)
            try:
                center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
            except ZeroDivisionError:
                pass

            # only proceed if the radius meets a minimum size
            if radius > 10:
                # draw the circle and centroid on the frame,
                # then update the list of tracked points
                cv2.circle(frame, (int(x), int(y)), int(radius), (0, 255, 255), 2)
                cv2.circle(frame, center, 5, (0, 0, 255), -1)

            rpixel = radius
            ypixel = constants.SCREEN_WIDTH / 2
            yinch = (ypixel * constants.BALL_RADIUS) / rpixel
            calibration = 1.5
            xinch = (yinch * constants.ARCTAN_30) * calibration

            centerx = x
            dpixel = centerx - 400
            dinch = (dpixel * constants.BALL_RADIUS) / rpixel
            alpha = (math.atan(dinch / xinch)) * 57.296

            return frame, xinch, alpha
        else:
            return frame, None, None

    def ball_val(self, frame):
        frame, cnts = self.contour(frame)
        frame, dist, angle = self.detect_ball(frame, cnts)
        return frame, dist, angle


class TapePipeline:
    def __init__(self, calib_fname: str = None):
        if calib_fname is None:
            raise TypeError("calib_fname (argument 2) must be str, not None")
        self.calibration_info = load_calibration_results(calib_fname)

    def process_image(
        self, image: np.array
    ) -> Tuple[
        List[np.array],
        np.array,
        Optional[np.array],
        Optional[np.array],
        Optional[float],
        Optional[np.array],
    ]:
        # image = imutils.resize(image, width=800)
        bitmask = self.generate_bitmask_camera(image)
        contours = self.get_contours(bitmask)
        corners_subpixel = self.get_corners(contours, bitmask)

        print(corners_subpixel)

        if len(corners_subpixel) < 1:
            return image, None, None

        try:
            rvec, tvec, dist = self.estimate_pose(corners_subpixel)
            euler_angles = self.rodrigues_to_euler_angles(rvec)
            dist_meters = dist * 0.3048
            angles_degree = math.degrees(euler_angles[0])
        except cv2.error:
            rvec, tvec, dist, euler_angles = None, None, None, None  # noqa: F841
            dist_meters = None
            angles_degree = None
        frame = cv2.drawContours(image, contours, -1, (255, 0, 0), thickness=3)

        return frame, dist_meters, angles_degree

    def generate_bitmask_camera(self, image: np.array) -> np.array:
        # image = cv2.blur(image, (7, 7))
        hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        im = cv2.inRange(hsv_image, lower_green, upper_green)
        closing = cv2.morphologyEx(im, cv2.MORPH_CLOSE, np.ones((3, 3)))
        # print(closing)
        return closing

    def get_contours(self, bitmask: np.array) -> List[np.array]:
        contours = cv2.findContours(bitmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = imutils.grab_contours(contours)
        contour_hull_areas = [
            cv2.contourArea(cv2.convexHull(contour)) for contour in contours
        ]
        is_candidate = []
        for contour, contour_hull_area in zip(contours, contour_hull_areas):
            if contour_hull_area > 10:
                area = cv2.contourArea(contour)
                if area / contour_hull_area > 0.85:
                    _, _, w, h = cv2.boundingRect(contour)
                    ratio = (
                        -constants.VISION_TAPE_ROTATED_WIDTH_FT
                        / constants.VISION_TAPE_ROTATED_HEIGHT_FT
                    )
                    if 0.5 * ratio <= w / h <= 1.5 * ratio:
                        is_candidate.append(True)
                        continue
            is_candidate.append(False)

        def approximate_contour(cnt):
            epsilon = 0.02 * cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, epsilon, True)
            return approx

        candidates = [
            approximate_contour(contour)
            for i, contour in enumerate(contours)
            if is_candidate[i]
        ]
        candidates.sort(key=lambda cnt: cv2.contourArea(cnt), reverse=True)
        return candidates

    def get_corners(self, contours: List[np.array], bitmask: np.array) -> np.array:
        contours = [x.reshape(-1, 2) for x in contours[:2]]
        tops = [min(contour, key=lambda x: x[1]) for contour in contours]
        bots = [max(contour, key=lambda x: x[1]) for contour in contours]
        tops.sort(key=lambda x: x[0])
        bots.sort(key=lambda x: x[0])
        pixel_corners = np.array(tops + bots, dtype=np.float32).reshape(-1, 1, 2)
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
        corners_subpixel = cv2.cornerSubPix(
            bitmask, pixel_corners, (5, 5), (-1, -1), criteria
        )
        return corners_subpixel

    def estimate_pose(
        self, corners_subpixel: np.array
    ) -> Tuple[np.array, np.array, float]:
        retval, rvec, tvec = cv2.solvePnP(
            constants.VISION_TAPE_OBJECT_POINTS,
            corners_subpixel,
            self.calibration_info.camera_matrix,
            self.calibration_info.dist_coeffs,
        )
        dist = np.linalg.norm(tvec)
        return rvec, tvec, dist

    def rodrigues_to_euler_angles(self, rvec):
        mat, jac = cv2.Rodrigues(rvec)
        sy = np.sqrt(mat[0, 0] * mat[0, 0] + mat[1, 0] * mat[1, 0])
        singular = sy < 1e-6
        if not singular:
            x = np.math.atan2(mat[2, 1], mat[2, 2])
            y = np.math.atan2(-mat[2, 0], sy)
            z = np.math.atan2(mat[1, 0], mat[0, 0])
        else:
            x = np.math.atan2(-mat[1, 2], mat[1, 1])
            y = np.math.atan2(-mat[2, 0], sy)
            z = 0
            print("")
        return np.array([x, y, z])


def save_calibration_results(
    camera_matrix: np.array,
    dist_coeffs: np.array,
    rvecs: np.array,
    tvecs: np.array,
    fisheye: bool,
    fname: str = "{}/calibration_info.pickle".format(os.path.dirname(__file__)),
):
    results = CalibrationResults(camera_matrix, dist_coeffs, rvecs, tvecs, fisheye)
    with open(fname, "wb") as f:
        pickle.dump(results, f)


def load_calibration_results(fname: str) -> CalibrationResults:
    with open(fname, "rb") as f:
        return pickle.load(f)
