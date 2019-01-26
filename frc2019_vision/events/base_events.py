from abc import ABCMeta, abstractmethod


class BaseEvent(metaclass=ABCMeta):
    @staticmethod
    @abstractmethod
    def event_id() -> str:
        pass


class BaseGetEvent(BaseEvent):
    @staticmethod
    def event_id() -> str:
        return "get"

    @staticmethod
    @abstractmethod
    def run() -> str:
        pass


class BaseSetEvent(BaseEvent):
    @staticmethod
    def event_id() -> str:
        return "set"

    @staticmethod
    @abstractmethod
    def run(arg) -> str:
        pass
