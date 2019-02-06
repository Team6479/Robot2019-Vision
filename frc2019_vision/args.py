from . import Target, environment


def parse_args(args: vars):
    environment.TARGET.put(args["target"])
    environment.GUI = args["gui"]
    environment.CAMERA_PORT = args["camera"]
    environment.NETIFACE = args["netiface"]


def target(arg: str):
    arg = arg.lower()
    for target in Target:
        if arg == target.value:
            return target
    return Target.NONE
