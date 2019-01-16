from . import Target, environment


def parse_args(args: vars):
    environment.TARGET = args["target"]
    environment.GUI = args["gui"]

def target(arg: str):
    arg = arg.lower()
    if arg == "ball":
        return Target.BALL
    elif arg == "tape":
        return Target.TAPE
    else:
        return Target.NONE
