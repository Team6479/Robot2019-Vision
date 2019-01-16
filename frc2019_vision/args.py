from . import Target, enviorment


def parse_args(args: vars):
    enviorment.TARGET = args["target"]
    enviorment.GUI = args["gui"]

def target(arg: str):
    arg = arg.lower()
    if arg == "ball":
        return Target.BALL
    elif arg == "tape":
        return Target.TAPE
    else:
        return Target.NONE
