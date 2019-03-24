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

PipelineResults = collections.namedtuple("PipelineResults",
                                         ['bitmask', 'trash', 'contours', 'corners', 'pose_estimation', 'euler_angles'])

PoseEstimation = collections.namedtuple("PoseEstimation", ['left_rvec', 'left_tvec', 'right_rvec', 'right_tvec'])
EulerAngles = collections.namedtuple("EulerAngles", ['left', 'right'])

PipelineResults._field_types = {'bitmask': np.array, 'contours': List[np.array], 'corners': List[np.array],
                                'pose_estimation': PoseEstimation, 'euler_angles': EulerAngles}

def avg(iter):
    try:
        return sum(iter)/len(iter)
    except ZeroDivisionError:
        return 0

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
        self.last_centroid_x = []
        self.width, self.height = 0
        if calib_fname is None:
            raise TypeError("calib_fname (argument 2) must be str, not None")
        self.calibration_info = load_calibration_results(calib_fname)

    def process_image(self, image: np.array) -> PipelineResults:

        bitmask = self.generate_bitmask_camera(image)
        contours, trash_contours = self.get_contours(bitmask)
        frame = cv2.drawContours(image, contours[:1], -1, (255, 0, 0), thickness=3)

        if len(contours) >= 2:
            return frame, None, None

        corners_subpixel = self.get_corners(contours, bitmask)

        try:
            result = self.estimate_pose(corners_subpixel)
            euler_angles = EulerAngles(
                self.rodrigues_to_euler_angles(result.left_rvec),
                self.rodrigues_to_euler_angles(result.right_rvec),
            )
        except (cv2.error, AttributeError):
            result, euler_angles = None, None

        return PipelineResults(bitmask, trash_contours, contours, corners_subpixel, result, euler_angles)

    def generate_bitmask_camera(self, image: np.array) -> np.array:
        image = cv2.blur(image, (7, 7))
        hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        im = cv2.inRange(hsv_image, lower_green, upper_green)
        closing = cv2.morphologyEx(im, cv2.MORPH_CLOSE, np.ones((3, 3)))
        return closing

    def get_contours(self, bitmask: np.array) -> Tuple[List[np.array], List[np.array]]:
        trash = []
        contours, hierarchy = cv2.findContours(bitmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        convex_hulls = [cv2.convexHull(contour) for contour in contours]
        contour_hull_areas = [cv2.contourArea(hull) for hull in convex_hulls]

        self.height = bitmask.shape[0]
        self.width = bitmask.shape[1]
        # print(height, width)

        def not_touching_edge(cnt):
            cnt = cnt.reshape((-1, 2))
            top_index = cnt[:, 1].argmin()
            bottom_index = cnt[:, 1].argmax()
            left_index = cnt[:, 0].argmin()
            right_index = cnt[:, 0].argmax()

            top_y = cnt[top_index][1]
            bot_y = cnt[bottom_index][1]
            left_x = cnt[left_index][0]
            right_x = cnt[right_index][0]

            return top_y > 10 and bot_y < height - 10 and left_x > 10 and right_index < width - 10


        is_candidate = []
        for contour, contour_hull_area in zip(contours, contour_hull_areas):
            if contour_hull_area > 10:
                area = cv2.contourArea(contour)
                if area / contour_hull_area > 0.85:
                    _, _, w, h = cv2.boundingRect(contour)
                    ratio = -constants.VISION_TAPE_ROTATED_WIDTH_FT / constants.VISION_TAPE_ROTATED_HEIGHT_FT
                    if 0.5 * ratio <= w / h <= 1.5 * ratio:
                        if not_touching_edge(contour):
                            is_candidate.append(True)
                            continue
            is_candidate.append(False)
            trash.append(contour)

        candidates = [convex_hulls[i] for i, contour in enumerate(contours) if is_candidate[i]]

        def get_centroid_x(cnt):
            all_x = cnt.reshape((-1, 2))[:, 0]
            return int(np.sum(all_x)/all_x.shape)
            # M = cv2.moments(cnt)
            # return int(M["m10"] / M["m00"])

        def is_tape_on_left_side(cnt):
            min_area_box = np.int0(cv2.boxPoints(cv2.minAreaRect(cnt)))

            left_box_point = min(min_area_box, key=lambda row: row[0])
            right_box_point = max(min_area_box, key=lambda row: row[0])

            return not left_box_point[1] < right_box_point[1]

        candidates.sort(key=get_centroid_x)

        if len(candidates) > 0:
            try:
                if not is_tape_on_left_side(candidates[0]):
                    trash.append(candidates[0])
                    del candidates[0]
                if is_tape_on_left_side(candidates[-1]):
                    trash.append(candidates[-1])
                    del candidates[-1]
            except Exception as e:
                pass

       if len(candidates) > 0:
            try:
                if not is_tape_on_left_side(candidates[0]):
                    trash.append(candidates[0])
                    del candidates[0]
                    # print("removed leftmost for pointing to right")
                if is_tape_on_left_side(candidates[-1]):
                    trash.append(candidates[-1])
                    del candidates[-1]
                    # print("removed rightmost for pointing to left")
            except Exception as e:
                #
                pass

        if len(candidates) > 1:
            contour_pair_centroids = {}

            for i, left_cnt, right_cnt in zip(range(len(candidates)), candidates[::2], candidates[1::2]):
                centroid = get_centroid_x(np.concatenate((left_cnt, right_cnt)))
                contour_pair_centroids[centroid] = i

            if len(contour_pair_centroids) > 0:
                if len(self.last_centroid_x) == 0:
                    self.last_centroid_x.append(min(contour_pair_centroids.keys(), key=lambda x: np.math.fabs(self.width/2 - x)))
                    avg_X = avg(self.last_centroid_x)
                else:
                    if len(self.last_centroid_x) > 5:
                        del self.last_centroid_x[0]
                    avg_X = avg(self.last_centroid_x)
                    self.last_centroid_x.append(min(contour_pair_centroids.keys(),
                                               key=lambda x: np.math.fabs(avg_X - x)))

                pair_num = contour_pair_centroids[self.last_centroid_x[-1]]

                left_index = pair_num * 2
                right_index = left_index + 1

                trash.extend(candidates[:left_index])
                trash.extend(candidates[right_index + 1:])
                candidates = [candidates[left_index], candidates[right_index]]
                # scandidates.sort(key=get_centroid_x)
                print(is_tape_on_left_side(candidates[0]))

                return candidates, trash  # left guaranteed to be first

        self.last_centroid_x = []
        return [], candidates + trash

    def get_corners(self, contours: List[np.array], bitmask: np.array) -> List[np.array]:

        contours = [x.reshape(-1, 2) for x in contours[:2]]

        def get_corners_intpixel_alternate(cnt):
            def removearray(L, arr):
                ind = 0
                size = len(L)
                while ind != size and not np.array_equal(L[ind], arr):
                    ind += 1
                if ind != size:
                    L.pop(ind)
                else:
                    raise ValueError('array not found in list.')

            blank = np.zeros(bitmask.shape).astype(np.uint8)
            cv2.drawContours(blank, [cnt], -1, (255,), thickness=cv2.FILLED)
            dst = cv2.goodFeaturesToTrack(image=blank, maxCorners=5, qualityLevel=0.16, minDistance=15).reshape(-1, 2)
            if len(dst) < 5:
                return get_corners_intpixel(cnt)

            points = list(dst)

            top_point = min(points, key=lambda x: x[1])
            removearray(points, top_point)

            fake_bottom_point = max(points, key=lambda x: x[1])
            removearray(points, fake_bottom_point)

            left_point = min(points, key=lambda x: x[0])
            removearray(points, left_point)

            right_point = max(points, key=lambda x: x[0])
            removearray(points, right_point)

            leftover_point = points[0]

            top_point, inner_pt, outer_pt, _ = get_corners_intpixel(cnt)

            if left_point[1] > right_point[1]:
                inner_pt, outer_pt = right_point, left_point
            else:
                inner_pt, outer_pt = left_point, right_point

            bot_point = constants.line_intersect(inner_pt, leftover_point, outer_pt, fake_bottom_point)

            return top_point, inner_pt, outer_pt, bot_point

        def get_corners_intpixel(cnt):
            top_index = cnt[:, 1].argmin()
            bottom_index = cnt[:, 1].argmax()
            left_index = cnt[:, 0].argmin()
            right_index = cnt[:, 0].argmax()

            top_point = cnt[top_index]
            bot_point = cnt[bottom_index]
            left_point = cnt[left_index]
            right_point = cnt[right_index]

            if left_point[1] > right_point[1]:
                return top_point, right_point, left_point, bot_point
            else:
                return top_point, left_point, right_point, bot_point

        corners = [np.array(get_corners_intpixel(cnt)).reshape((-1, 1, 2)) for cnt in contours]

        corners_subpixel = [cv2.cornerSubPix(bitmask,
                                             corner.astype(np.float32),
                                             (5, 5), (-1, -1),
                                             constants.SUBPIXEL_CRITERIA) for corner in corners]

        return corners_subpixel

    def estimate_pose(self, corners_subpixel: List[np.array]) -> PoseEstimation:

        result = {"left": None, "right": None}

        for name, corners, objp in zip(result.keys(), corners_subpixel, (constants.VISION_TAPE_OBJECT_POINTS_LEFT_SIDE, constants.VISION_TAPE_OBJECT_POINTS_RIGHT_SIDE)):
            # NOTE: If using solvePnPRansac, retvals are retval, rvec, tvec, inliers
            if self.calibration_info.fisheye:
                undistorted_points = cv2.fisheye.undistortPoints(corners, self.calibration_info.camera_matrix,
                                                                 self.calibration_info.dist_coeffs)[1:]
                result[name] = cv2.solvePnP(objp,
                                            undistorted_points,
                                            self.calibration_info.camera_matrix,
                                            None)
            else:
                result[name] = cv2.solvePnP(objp,
                                            corners,
                                            self.calibration_info.camera_matrix,
                                            self.calibration_info.dist_coeffs)[1:]

        try:
            return PoseEstimation(result['left'][0], result['left'][1], result['right'][0], result['right'][1])
        except TypeError:
            return None

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
