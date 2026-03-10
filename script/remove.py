from script.utils.constant import *
from script.utils import logutil
from pathlib import Path

import shutil

def run(vers: list[str]):
    log = logutil.Logger("remove").get_log()
    for platform in [PlatForm.MODRINTH, PlatForm.CURSEFORGE]:
        for dir_ver in vers:
            path = Path(platform).joinpath(dir_ver)
            if path.exists():
                shutil.rmtree(path)
                log.info(f"{platform}-{dir_ver} remove successful!")
