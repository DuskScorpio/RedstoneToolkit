from script.utils.constant import *
from pathlib import Path

import os
import re


def get_dir_vers(platform: PlatForm) -> list[str]:
    if platform == PlatForm.ALL:
        assert TypeError
    dir_path = Path(platform)
    return [i.name for i in dir_path.iterdir() if i.is_dir() and dir_path.joinpath(i.name).joinpath("pack.toml").exists()]


def get_dir_mods(platform: PlatForm, ver: str) -> list[str]:
    if platform == PlatForm.ALL:
        assert TypeError
    mod_path = Path(platform).joinpath(ver).joinpath("mods")
    if not mod_path.exists():
        return []
    return [f.name.replace(".pw.toml", "") for f in mod_path.iterdir() if f.is_file() and re.match(".*\\.pw\\.toml", f.name)]



if __name__ == "__main__":
    path = Path(__file__).resolve().parent.parent.parent
    os.chdir(path)
    print(get_dir_mods(PlatForm.MODRINTH, "1.21.11"))