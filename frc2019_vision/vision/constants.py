import math
import os

import cv2
import numpy as np


def _rot_mat(rad):
    return np.array([[math.cos(rad), -math.sin(rad)], [math.sin(rad), math.cos(rad)]])


def linear_interpolate(point_a, point_b, num_points):
    num_points = int(num_points)

    def line_func(t):
        return (1 - t) * point_a + t * point_b

    return [line_func(t / num_points) for t in range(0, num_points + 1)]


# Ball dimensions
SCREEN_WIDTH = 800
"""Width of the modified screen"""

SCREEN_HEIGHT = 600
"""Height of the modified screen"""

BALL_RADIUS = 6.5
"""Radius of the ball"""

CAMERA_ANGLE = 60
"""Field of view of the camera"""

ARCTAN_30 = 1.537
"""Arctan of 30"""

VISION_TAPE_LENGTH_IN = 5.5
"""Length of the vision tape (inches)"""

VISION_TAPE_LENGTH_FT = VISION_TAPE_LENGTH_IN / 12
"""Length of the vision tape (feet)"""

VISION_TAPE_WIDTH_IN = 2
"""Width of the vision tape (inches)"""

VISION_TAPE_WIDTH_FT = 2 / 12
"""Width of the vision tape (feet)"""

# Vision tape angles
VISION_TAPE_ANGLE_FROM_VERT_DEG = 14.5
"""Angle between the vision tape and the vertical axis (degrees)"""

VISION_TAPE_ANGLE_FROM_VERT_RAD = math.radians(VISION_TAPE_ANGLE_FROM_VERT_DEG)
"""Angle between the vision tape and the vertical axis (radians)"""

VISION_TAPE_ANGLE_FROM_HORIZONTAL_DEG = 90 - VISION_TAPE_ANGLE_FROM_VERT_DEG
"""Angle between the vision tape and the horizontal axis (degrees)"""

VISION_TAPE_ANGLE_FROM_HORIZONTAL_RAD = math.radians(
    VISION_TAPE_ANGLE_FROM_HORIZONTAL_DEG
)
"""Angle between the vision tape and the horizontal axis (radians)"""

# Vision tape relative geometry
VISION_TAPE_MIN_SEPARATION_IN = 8
"""Distance between the two pieces of vision tape at their closest point (inches)"""

VISION_TAPE_MIN_SEPARATION_FT = VISION_TAPE_MIN_SEPARATION_IN / 12
"""Distance between the two pieces of vision tape at their closest point (feet)"""

VISION_TAPE_TOP_SEPARATION_IN = (
    2 * VISION_TAPE_WIDTH_IN * math.sin(VISION_TAPE_ANGLE_FROM_HORIZONTAL_RAD)
    + VISION_TAPE_MIN_SEPARATION_IN
)
"""Distance between the top point on the left rectangle and the top point on the right rectangle (inches)"""

VISION_TAPE_TOP_SEPARATION_FT = VISION_TAPE_TOP_SEPARATION_IN / 12
"""Distance between the top point on the left rectangle and the top point on the right rectangle (feet)"""

VISION_TAPE_BOTTOM_SEPARATION_IN = (
    2 * VISION_TAPE_LENGTH_IN * math.sin(VISION_TAPE_ANGLE_FROM_VERT_RAD)
    + VISION_TAPE_MIN_SEPARATION_IN
)
"""Distance between the bottom point on the left rectangle and the bottom point on the right rectangle (inches)"""

VISION_TAPE_BOTTOM_SEPARATION_FT = VISION_TAPE_BOTTOM_SEPARATION_IN / 12
"""Distance between the bottom point on the left rectangle and the bottom point on the right rectangle (feet)"""

VISION_TAPE_ROTATED_HEIGHT_FT = np.matmul(
    _rot_mat(-VISION_TAPE_ANGLE_FROM_VERT_RAD),
    np.array([VISION_TAPE_WIDTH_FT, -VISION_TAPE_LENGTH_FT]),
)[1]

VISION_TAPE_ROTATED_WIDTH_FT = np.matmul(
    _rot_mat(-VISION_TAPE_ANGLE_FROM_VERT_RAD),
    np.array([VISION_TAPE_WIDTH_FT, VISION_TAPE_LENGTH_FT]),
)[0]

CENTER_LOC_FT = np.array(
    [VISION_TAPE_TOP_SEPARATION_FT / 2, VISION_TAPE_ROTATED_HEIGHT_FT / 2]
)

# Vision tape coordinates
TOP_LEFT_LOCATION_FT = np.array([0, 0])

BOTTOM_LEFT_LOCATION_FT = np.array([0, -VISION_TAPE_LENGTH_FT])

TOP_RIGHT_LOCATION_FT = np.array([VISION_TAPE_WIDTH_FT, 0])

BOTTOM_RIGHT_LOCATION_FT = np.array([VISION_TAPE_WIDTH_FT, -VISION_TAPE_LENGTH_FT])

_two_to_three = np.array([[1, 0], [0, 1], [0, 0]])

_reflect_across_y_axis = np.array([[-1, 0, 0], [0, 1, 0], [0, 0, 0]])


def tape_corners_to_obj_points(top_left, top_right, bottom_left, bottom_right, k=5):
    return np.array(
        # linear_interpolate(top_left, top_right, 2 * k) +
        # # linear_interpolate(top_right, bottom_right, 5.5 * k)  +
        # # linear_interpolate(bottom_right, bottom_left, 2 * k) +
        # linear_interpolate(bottom_left, top_left, 5.5 * k)
        [top_left, top_right, bottom_left, bottom_right]
    )


def line_intersect(*args) -> np.array:
    assert len(args) == 4, "Needs exactly 4 points"
    a1, a2, b1, b2 = [p.reshape((2,)) for p in args]

    t, s = np.linalg.solve(np.array([a2 - a1, b2 - b1]).T, b1 - a1)

    return a1 * (1 - t) + a2 * t


VISION_TAPE_OBJECT_POINTS_LEFT_SIDE = np.array(
    [
        np.matmul(
            _two_to_three,
            np.matmul(_rot_mat(-VISION_TAPE_ANGLE_FROM_VERT_RAD), TOP_LEFT_LOCATION_FT),
        ),
        np.matmul(
            _two_to_three,
            np.matmul(
                _rot_mat(-VISION_TAPE_ANGLE_FROM_VERT_RAD), TOP_RIGHT_LOCATION_FT
            ),
        ),
        np.matmul(
            _two_to_three,
            np.matmul(
                _rot_mat(-VISION_TAPE_ANGLE_FROM_VERT_RAD), BOTTOM_LEFT_LOCATION_FT
            ),
        ),
        np.matmul(
            _two_to_three,
            np.matmul(
                _rot_mat(-VISION_TAPE_ANGLE_FROM_VERT_RAD), BOTTOM_RIGHT_LOCATION_FT
            ),
        ),
    ]
)
"""Parameter to cv2.solvePnP and cv2.solvePnPRansac"""

VISION_TAPE_OBJECT_POINTS_RIGHT_SIDE = np.array(
    [
        np.matmul(_reflect_across_y_axis, objp)
        for objp in VISION_TAPE_OBJECT_POINTS_LEFT_SIDE
    ]
)

CAMERA_ID = int(0)
"""The id of the camera"""

CALIBRATION_FILE_LOCATION = "{}/prod_camera_calib.pickle".format(
    os.path.dirname(__file__)
)
"""The path to the pickle containing the calibration information"""

SUBPIXEL_CRITERIA = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
