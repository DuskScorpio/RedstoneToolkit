from pathlib import Path
from ruamel.yaml import YAML
from subprocess import Popen, PIPE
from semantic_version import Version, NpmSpec
from loguru import logger

import re
import sys
import tomllib
import tomli_w


FILE_PATH = "../mod_list.yml"
PACKWIZ = "../tools/packwiz"


# install mods
def main():
    yaml = YAML()
    with open(FILE_PATH, "r", encoding="utf-8") as f:
        data = yaml.load(f)
    mods_dict: dict = data["mods"]
    disable_mods_dict:dict = data["disable_mods"]
    mc_ver_list = [f.name for f in list(Path("../").glob("*/")) if f.joinpath("pack.toml").exists()]

    remove_mod(mc_ver_list, {**mods_dict, **disable_mods_dict}) # remove mod
    clean_log(mc_ver_list) # clean log

    for mc_ver in mc_ver_list:
        path = "../{}".format(mc_ver)
        mc_semver = Version(mc_ver)
        for mod in mods_dict:
            condition = NpmSpec(mods_dict[mod])
            if not Path("{}/mods/{}.pw.toml".format(path, mod)).exists() and condition.match(mc_semver):
                install_mod(path, mod, mc_ver)
            enable(mc_ver, mod)

        for mod in disable_mods_dict:
            condition = NpmSpec(disable_mods_dict[mod])
            if not Path("{}/mods/{}.pw.toml".format(path, mod)).exists() and condition.match(mc_semver):
                install_mod(path, mod, mc_ver)
            disable(mc_ver, mod)

        # tomil-w changes something, so it needs to be refreshed
        process = Popen([PACKWIZ, "refresh"], cwd=path, stdout=PIPE, text=True, bufsize=1)
        set_logger(mc_ver, "DEBUG")
        for e in process.stdout:
            text = e.strip()
            logger.info(text)


def clean_log(mc_ver_list: list[str]):
    for mc_ver in mc_ver_list:
        path = Path("../logs/{}-install.log".format(mc_ver))
        path.unlink(missing_ok=True)


def install_mod(path: str, name: str, mc_ver: str):
    set_write_logger(mc_ver, "DEBUG", "WARNING")
    process = Popen(
        [PACKWIZ, "mr", "add", name],
        cwd=path,
        text=True,
        stdout=PIPE,
        stderr=PIPE,
        stdin=PIPE,
        bufsize=1
    )

    # Don't change these, because it works by mystical powers
    flag = False
    for e in process.stdout:
        text = e.strip()
        if text == "Dependencies found:":
            flag = True
        if flag:
            process.stdin.write("n\n")
            process.stdin.flush()
        logger.info(text)
        if re.match("Failed to add project:.*", text):
            logger.warning("{} install failed!".format(name))
    process.wait()


def remove_mod(mc_ver_list: list[str], mods: dict[str, str]):
    for mc_ver in mc_ver_list:
        set_logger(mc_ver, "DEBUG")
        mc_dir = Path("../{}".format(mc_ver))
        mods_dir = mc_dir.joinpath("mods")
        if not mods_dir.exists():
            continue
        files = [f.name for f in mods_dir.iterdir() if f.is_file()]
        dir_mods = [f.replace(".pw.toml", "") for f in files if re.match(".*\\.pw\\.toml", f)]
        for mod in dir_mods:
            should_remove = False
            if mod not in mods:
                should_remove = True
            else:
                mc_semver = Version(mc_ver)
                condition = NpmSpec(mods[mod])
                if not condition.match(mc_semver):
                    should_remove = True
            if should_remove:
                process = Popen(
                    [PACKWIZ, "remove", mod],
                    stdout=PIPE,
                    cwd=mc_dir,
                    text=True,
                    bufsize=1
                )
                for line in process.stdout:
                    logger.info(line.strip())
                process.wait()


def disable(mc_version: str, mod_name: str):
    path = "../{0}/mods/{1}.pw.toml".format(mc_version, mod_name)
    if not Path(path).exists():
        return
    with open(path, "rb") as f:
        data = tomllib.load(f)
    original_name = data["filename"]
    if re.match(".*\\.disabled", original_name):
        return
    data["filename"] = original_name + ".disable"
    with open(path, "wb") as f:
        tomli_w.dump(data, f)


def enable(mc_version: str, mod_name: str):
    path = "../{0}/mods/{1}.pw.toml".format(mc_version, mod_name)
    if not Path(path).exists():
        return
    with open(path, "rb") as f:
        data = tomllib.load(f)
    original_name = data["filename"]
    if re.match(".*\\.disabled", original_name):
        data["filename"] = str(original_name).replace(".disabled", "")
        with open(path, "wb") as f:
            tomli_w.dump(data, f)


def set_write_logger(mc_ver: str, level_stdout: str, level_file: str):
    # DEBUG WARNING
    logger.remove()
    logger.add(
        sink=sys.stdout,
        format="<green>[{time:HH:mm:ss}]</green> <level>[{level}/(" + mc_ver + ")]</level>: <level>{message}</level>",
        level=level_stdout,
        colorize=True
    )
    logger.add(
        sink="../logs/{}-install.log".format(mc_ver),
        format="[{time:HH:mm:ss}] [{level}/(" + mc_ver + ")]: {message}",
        level=level_file
    )


def set_logger(mc_ver: str, level_stdout: str):
    # DEBUG WARNING
    logger.remove()
    logger.add(
        sink=sys.stdout,
        format="<green>[{time:HH:mm:ss}]</green> <level>[{level}/(" + mc_ver + ")]</level>: <level>{message}</level>",
        level=level_stdout,
        colorize=True
    )


if __name__ == "__main__":
    main()