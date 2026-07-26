import tomllib
from pathlib import Path

import tomli_w
from semantic_version import validate

from script.utils import logutil, util
from script.utils.constant import *


def run(match: str, version: str, platforms: list[PlatformSource]):
    log = logutil.get_log("update_version", False)
    if not validate(version):
        log.error(f"Invalid version format '{version}'. Expected format: X.Y.Z")
        return

    for platform in platforms:
        dirs = util.get_dir_vers(platform)
        for mc_dir in dirs:
            path = Path(platform).joinpath(mc_dir).joinpath("pack.toml")
            if not util.check_match(match, mc_dir):
                continue
            with open(path, "rb") as fr:
                data = tomllib.load(fr)

            data["version"] = version

            with open(path, "wb") as fw:
                tomli_w.dump(data, fw)
            log.info(f"Updating '{platform}/{mc_dir}' pack.toml files to version {version}")
