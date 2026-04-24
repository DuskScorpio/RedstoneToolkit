from script.utils import logutil, util
from script.utils.constant import *
from pathlib import Path
from semantic_version import validate

import tomllib
import tomli_w


def run(match: str, version: str, platform: PlatForm):
    log = logutil.Logger("update_version").get_log()
    if not validate(version):
        log.error(f"Invalid version format '{version}'. Expected format: X.Y.Z")
        return

    platform_map = {
        PlatForm.MODRINTH: [PlatForm.MODRINTH],
        PlatForm.CURSEFORGE: [PlatForm.CURSEFORGE],
        PlatForm.ALL: [PlatForm.MODRINTH, PlatForm.CURSEFORGE]
    }
    for hit_platform in platform_map[platform]:
        dirs = util.get_dir_vers(hit_platform)
        for mc_dir in dirs:
            path = Path(hit_platform).joinpath(mc_dir).joinpath("pack.toml")
            if not util.check_match(match, mc_dir):
                continue
            with open(path, "rb") as fr:
                data = tomllib.load(fr)

            data["version"] = version

            with open(path, "wb") as fw:
                tomli_w.dump(data, fw)
            log.info(f"Updating '{hit_platform}/{mc_dir}' pack.toml files to version {version}")
