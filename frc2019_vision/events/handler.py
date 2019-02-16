
from . import assemble_message, get_events, set_events  # noqa: F401
from .base_events import BaseGetEvent, BaseSetEvent


GET_EVENTS: dict = {}
SET_EVENTS: dict = {}


def index():
    base_events: tuple = [BaseGetEvent, BaseSetEvent]
    for base_event in base_events:
        base_event_id: str = base_event.event_id()
        for event in base_event.__subclasses__():
            if base_event_id == "get":
                GET_EVENTS[event.event_id()] = event
            elif base_event_id == "set":
                SET_EVENTS[event.event_id()] = event


def parse(data: list) -> str:
    command = data[0]
    try:
        keyword = data[1]
    except IndexError:
        return assemble_message("No keyword supplied", True)

    if command == "GET":
        if keyword in GET_EVENTS.keys():
            return GET_EVENTS[keyword].run()
        else:
            return assemble_message("Invalid keyword for GET", True)
    elif command == "SET":
        if keyword in SET_EVENTS.keys():
            if len(data) > 2:
                return SET_EVENTS[keyword].run(data[2])
            else:
                return assemble_message("Arg not supplied for SET", True)
        else:
            return assemble_message("Invalid keyword for SET", True)
    else:
        return assemble_message("Invalid command: {}".format(command), True)
