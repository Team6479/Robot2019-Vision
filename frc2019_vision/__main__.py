import argparse

import cv2

from . import args, core, environment, vision


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target", type=args.target, help="object to detect")
    ap.add_argument("-g", "--gui", action='store_true', help="tell application to display a window")
    args.parse_args(vars(ap.parse_args()))

    if environment.GUI:
        vision.create_windows()

    core.start_loop()

    # if we are not using a video file, stop the camera video stream
    environment.VIDEO_STREAM.stop()

    # close all windows
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
