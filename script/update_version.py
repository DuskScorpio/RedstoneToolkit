from script.utils import logutil, util
from script.utils.constant import *
from pathlib import Path
from semantic_version import validate, NpmSpec, Version

import tomllib
import tomli_w


def run(match: str, version: str):
    log = logutil.Logger("update_version").get_log()
    if not validate(version):
        log.error(f"Invalid version format '{version}'. Expected format: X.Y.Z")
        return

    platforms = [PlatForm.MODRINTH, PlatForm.CURSEFORGE]
    for platform in platforms:
        dirs = util.get_dir_vers(platform)
        for mc_dir in dirs:
            path = Path(platform).joinpath(mc_dir).joinpath("pack.toml")
            if not path.exists() or not util.validate_condition(match) or not NpmSpec(match).match(Version(mc_dir)):
                continue
            with open(path, "rb") as fr:
                data = tomllib.load(fr)

            data["version"] = version

            with open(path, "wb") as fw:
                tomli_w.dump(data, fw)
            log.info(f"Updating '{platform}/{mc_dir}' pack.toml files to version {version}")
