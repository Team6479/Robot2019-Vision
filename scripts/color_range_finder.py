import argparse
import cv2


cap = cv2.VideoCapture(0)
parser = argparse.ArgumentParser()
parser.add_argument(
    "--invert",
    help="Invert the image before computing the bitmask",
    action="store_true",
)
parser.add_argument(
    "--exposure",
    help="Set Exposure to competition value",
    action="store_true"
)
args = parser.parse_args()

_, image = cap.read()  # picture from my webcam
hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

low = [0, 0, 0]
high = [360, 255, 255]

im = cv2.inRange(hsv_image, tuple(low), tuple(high))


def on_trackbar(name, val, low, high):
    if name == "low_h":
        low[0] = val
    elif name == "low_s":
        low[1] = val
    elif name == "low_v":
        low[2] = val
    elif name == "high_h":
        high[0] = val
    elif name == "high_s":
        high[1] = val
    elif name == "high_v":
        high[2] = val


cv2.imshow("bitmask", im)
cv2.imshow("orig", image)
smaller_max = 255

cv2.createTrackbar(
    "low_h", "bitmask", 0, 360, lambda v: on_trackbar("low_h", v, low, high)
)
cv2.createTrackbar(
    "low_s", "bitmask", 0, smaller_max, lambda v: on_trackbar("low_s", v, low, high)
)
cv2.createTrackbar(
    "low_v", "bitmask", 0, smaller_max, lambda v: on_trackbar("low_v", v, low, high)
)
cv2.createTrackbar(
    "high_h", "bitmask", 360, 360, lambda v: on_trackbar("high_h", v, low, high)
)
cv2.createTrackbar(
    "high_s", "bitmask", smaller_max, smaller_max, lambda v: on_trackbar("high_s", v, low, high)
)
cv2.createTrackbar(
    "high_v", "bitmask", smaller_max, smaller_max, lambda v: on_trackbar("high_v", v, low, high)
)

while True:
    ret, frame = cap.read()
    if args.invert:
        frame = cv2.bitwise_not(frame)
    if args.exposure:
        cap.set(cv2.CAP_PROP_EXPOSURE, 3)
    else:
        cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)    
    cv2.imshow("orig", frame)
    im = cv2.inRange(cv2.cvtColor(frame, cv2.COLOR_BGR2HSV), tuple(low), tuple(high))
    cv2.imshow("bitmask", im)
    cv2.waitKey(1000 // 30)

cv2.waitKey()
