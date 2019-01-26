import cv2

from .. import environment


def imshow(name: str, frame):
    if environment.GUI:
        cv2.imshow(name, frame)


def draw_crosshairs(frame):
    # Draw main vertical line
    cv2.line(frame, (400, 0), (400, 600), (0, 0, 255), 2)
    # Draw main horizontal line
    cv2.line(frame, (0, 300), (800, 300), (0, 0, 255), 2)

    # Draw two guide lines
    cv2.line(frame, (350, 100), (350, 500), (0, 0, 255), 2)
    cv2.line(frame, (450, 100), (450, 500), (0, 0, 255), 2)
