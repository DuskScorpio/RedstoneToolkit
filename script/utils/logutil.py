from logging import FileHandler, Formatter, INFO, DEBUG
from pathlib import Path
from datetime import datetime
from functools import cache

from colorlog import StreamHandler, getLogger, ColoredFormatter


class Logger:
    def __init__(self, name: str, write: bool = True):
        self.clean_log(name)
        self.logger = getLogger(name)
        self.logger.setLevel(DEBUG)

        handler = StreamHandler()
        handler.setFormatter(
            ColoredFormatter(
                fmt="[%(bold_green)s%(asctime)s%(reset)s] " +
                    "[%(log_color)s%(levelname)s%(reset)s/%(name)s]: " +
                    "%(message)s",
                datefmt="%Y-%m-%d/%H:%M:%S",
                log_colors={
                    "DEBUG": "cyan",
                    "INFO": "green",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "red,bg_white"
                }
            )
        )
        handler.setLevel(DEBUG)
        self.logger.addHandler(handler)

        if write:
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            file_name = datetime.now().strftime(f"{name}-%Y-%m-%d_%H_%M_%S")
            file_path = log_dir.joinpath(f"{file_name}.log")
            file_handler = FileHandler(file_path, mode="w", encoding='utf-8')
            file_handler.setFormatter(
                Formatter(
                    fmt="[%(asctime)s] [%(levelname)s/%(name)s]: %(message)s",
                    datefmt="%Y-%m-%d/%H:%M:%S"
                )
            )
            file_handler.setLevel(INFO)
            self.logger.addHandler(file_handler)

    def get_logger(self):
        return self.logger

    @staticmethod
    def clean_log(name: str):
        log_path = Path("log")
        if not log_path.exists() or not log_path.is_dir():
            return

        def sort_time(path: Path):
            path_name = path.name.replace(".log", "")
            return datetime.strptime(path_name, f"{name}-%Y-%m-%d_%H_%M_%S")

        file_path = [i for i in log_path.iterdir() if i.is_file() and i.name.startswith(f"{name}-")]
        file_path.sort(key=sort_time)
        if len(file_path) > 4:
            for i in file_path[0: len(file_path) - 4]:
                i.unlink()


@cache
def get_log(name: str, write: bool = True):
    return Logger(name, write).get_logger()
