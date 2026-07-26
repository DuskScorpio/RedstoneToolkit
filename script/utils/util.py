import re
from pathlib import Path
from typing import Literal

from semantic_version import NpmSpec, Version

from script.utils.constant import *


def get_dir_vers(platform: PlatformSource | PlatFormLegacy) -> list[str]:
    if platform == PlatFormLegacy.ALL:
        assert TypeError
    dir_path = Path(platform)
    return [i.name for i in dir_path.iterdir() if
            i.is_dir() and dir_path.joinpath(i.name).joinpath("pack.toml").exists()]


def get_dir_mods(platform: PlatformSource | PlatFormLegacy, mc_ver: str) -> list[str]:
    if platform == PlatFormLegacy.ALL:
        assert TypeError
    mod_path = Path(platform).joinpath(mc_ver).joinpath("mods")
    if not mod_path.exists():
        return []
    return [f.name.replace(".pw.toml", "") for f in mod_path.iterdir() if
            f.is_file() and re.match(".*\\.pw\\.toml", f.name)]


def validate_condition(condition: str) -> bool:
    try:
        NpmSpec(condition)
        return True
    except ValueError:
        return False


def check_match(match: str, version: str) -> bool:
    if not validate_condition(match):
        return False
    return NpmSpec(match).match(Version(version))


def get_platform_list(platform: Literal["modrinth", "curseforge", "all"]):
    match platform:
        case "modrinth":
            return PlatformSourceList.MODRINTH.value
        case "curseforge":
            return PlatformSourceList.CURSEFORGE.value
        case "all":
            return PlatformSourceList.ALL.value
        case _:
            raise ValueError
