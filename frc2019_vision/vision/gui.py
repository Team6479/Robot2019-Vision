import cv2

from . import constants
from .. import environment


def imshow(name: str, frame):
    if environment.GUI:
        cv2.imshow(name, frame)


def draw_crosshairs(frame):
    half_width = int(constants.SCREEN_WIDTH / 2)
    half_height = int(constants.SCREEN_HEIGHT / 2)
    # Draw main vertical line
    cv2.line(frame, (half_width, 0), (half_width, constants.SCREEN_HEIGHT), (0, 0, 255), 2)  # noqa: E501
    # Draw main horizontal line
    cv2.line(frame, (0, half_height), (constants.SCREEN_WIDTH, half_height), (0, 0, 255), 2)  # noqa: E501

    # Draw two guide lines
    cv2.line(frame, (half_height + 50, 100), (half_height + 50, 500), (0, 0, 255), 2)  # noqa: E501
    cv2.line(frame, (half_width + 50, 100), (half_width + 50, 500), (0, 0, 255), 2)  # noqa: E501
