from loguru import logger
from enum import Enum, auto

import sys


class Level(Enum):
    DEBUG = auto()
    INFO = auto()
    WARNING = auto()


class Logger:
    def __init__(
            self,
            name: str,
            write: bool=False,
            log_name: str="",
            level_c: Level=Level.INFO,
            level_f: Level=Level.INFO
    ):
        self.logger = logger.bind(name=name)
        self.logger.remove()
        self.level_c = level_c.name
        self.level_f = level_f.name
        self.__add_console()
        self.log_name = log_name
        if write:
            self.__add_file()


    def __add_console(self):
        self.logger.add(
            sink=sys.stdout,
            format="<green>[{time:HH:mm:ss}]</green> <level>[{level}/({extra[name]})]</level>: <level>{message}</level>",
            level=self.level_c,
            colorize=True
        )


    def __add_file(self):
        self.logger.add(
            sink="../logs/{}".format(self.log_name),
            format="[{time:HH:mm:ss}] [{level}/({extra[name]})]: {message}",
            level=self.level_f
        )


    def get_log(self):
        return self.logger