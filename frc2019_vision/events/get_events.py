from . import assemble_message
from .. import environment
from .base_events import BaseGetEvent


class GetPing(BaseGetEvent):
    @staticmethod
    def event_id() -> str:
        return "ping"

    @staticmethod
    def run() -> str:
        return assemble_message("pong")


class GetPosition(BaseGetEvent):
    @staticmethod
    def event_id() -> str:
        return "position"

    @staticmethod
    def run() -> str:
        string = "{0},{1}".format(environment.DISTANCE_FROM_OBJECT.get(), environment.ANGLE_FROM_CENTER.get())
        return assemble_message(string)
