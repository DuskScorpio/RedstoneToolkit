import shutil
from pathlib import Path

from script.utils import logutil
from script.utils.constant import *


def run(vers: list[str]):
    log = logutil.get_log("remove", False)
    for platform in PlatformSource:
        for dir_ver in vers:
            path = Path(platform).joinpath(dir_ver)
            if path.exists():
                shutil.rmtree(path)
                log.info(f"{platform}-{dir_ver} remove successful!")
