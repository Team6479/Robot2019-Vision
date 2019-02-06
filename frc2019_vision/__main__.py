import argparse
import sys

from . import args, threads
from .events import handler


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target", type=args.target, help="object to detect")
    ap.add_argument(
        "-g", "--gui", action="store_true", help="tell application to display a window"
    )
    ap.add_argument("-c", "--camera", type=int, default=0, help="specify camera port")
    ap.add_argument("-n", "--netiface", type=str, default="eth0", help="specify network interface")
    args.parse_args(vars(ap.parse_args()))

    handler.index()

    threads.create()
    threads.start()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        threads.stop()
        sys.exit(0)
