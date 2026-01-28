from pathlib import Path
from ruamel.yaml import YAML
from subprocess import run
from semantic_version import Version, SimpleSpec
from loguru import logger

import re
import sys
import tomllib
import tomli_w


FILE_PATH = "../mod_list.yml"


# install mods
def main():
    yaml = YAML()
    with open(FILE_PATH, "r", encoding="utf-8") as f:
        data = yaml.load(f)
    mods_dict: dict = data["mods"]
    disable_mods_dict:dict = data["disable_mods"]
    mc_ver_list = [f.name for f in list(Path("../").glob("*/")) if f.joinpath("pack.toml").exists()]

    remove_mod(mc_ver_list, [*mods_dict.keys(), *disable_mods_dict.keys()]) # remove mod
    clean_log(mc_ver_list) # clean log

    # install and disable mod
    for mc_ver in mc_ver_list:
        path = "../{}".format(mc_ver)
        mc_semver = Version(mc_ver)
        for mod in mods_dict:
            condition = SimpleSpec(mods_dict[mod])
            if condition.match(mc_semver):
                install_mod(path, mod, mc_ver)

        for disable_mod in disable_mods_dict:
            condition = SimpleSpec(disable_mods_dict[disable_mod])
            if condition.match(mc_semver):
                install_mod(path, disable_mod, mc_ver)
                disable(mc_ver, disable_mod)

        # tomil-w changes something, so it needs to be refreshed
        run(["../tools/packwiz", "refresh"], cwd=path)


def clean_log(mc_ver_list: list[str]):
    for mc_ver in mc_ver_list:
        path = Path("../logs/{}-update.log".format(mc_ver))
        path.unlink(missing_ok=True)


def install_mod(path: str, name: str, mc_ver: str):
    result = run(["../tools/packwiz", "mr", "add", name, "--yes"], cwd=path, capture_output=True, text=True)
    logger.remove()
    logger.add(
        sink=sys.stdout,
        format="<green>[{time:HH:mm:ss}]</green> <level>[{level}/(" + mc_ver +")]</level>: <level>{message}</level>",
        level="DEBUG",
        colorize=True
    )
    logger.add(
        sink="../logs/{}-install.log".format(mc_ver),
        format="[{time:HH:mm:ss}] [{level}/(" + mc_ver + ")]: {message}",
        level="WARNING"
    )
    logger.info(result.stdout)
    if re.match("Failed to add project:.*", result.stdout):
        logger.warning("{} install failed!".format(name))
    logger.remove()


def remove_mod(mc_versions: list[str], mods: list[str]):
    for mc_version in mc_versions:
        mc_dir = Path("../{}".format(mc_version))
        mods_dir = mc_dir.joinpath("mods")
        if not mods_dir.exists():
            continue
        files = [f.name for f in mods_dir.iterdir() if f.is_file()]
        dir_mods = [f.replace(".pw.toml", "") for f in files if re.match(".*\\.pw\\.toml", f)]
        for dir_mod in dir_mods:
            if dir_mod not in mods:
                run(["../tools/packwiz", "remove", dir_mod], cwd=mc_dir)



def disable(mc_version: str, mod_name: str):
    path = "../{0}/mods/{1}.pw.toml".format(mc_version, mod_name)
    if not Path(path).exists():
        return
    with open(path, "rb") as f:
        data = tomllib.load(f)
    original_name = data["filename"]
    data["filename"] = original_name + ".disable"
    with open(path, "wb") as f:
        tomli_w.dump(data, f)


if __name__ == "__main__":
    main()