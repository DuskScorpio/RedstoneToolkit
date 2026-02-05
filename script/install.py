from pathlib import Path
from ruamel.yaml import YAML
from subprocess import Popen, PIPE
from argparse import ArgumentParser
from semantic_version import Version, NpmSpec
from loguru import logger
from utils.install_util import Install
from utils.constant import *

import re
import os
import sys


# install mods
def main():
    parser = ArgumentParser()
    parser.add_argument('-v')
    arg = parser.parse_args()

    mc_dir_list = [f.name for f in list(Path("../").glob("*/")) if f.joinpath("pack.toml").exists()]
    if (arg.v is not None) and (arg.v not in mc_dir_list): raise ValueError
    yaml = YAML()
    with open(FILE_PATH, "r", encoding="utf-8") as f:
        data = yaml.load(f)
    enabled_file_list: list[dict[str, str]] = data[ENABLED]
    disabled_file_list: list[dict[str, str]] = data[DISABLED]

    remove_mod(mc_dir_list, [*enabled_file_list, *disabled_file_list]) # remove mod
    clean_log(mc_dir_list) # clean log

    for mc_dir in mc_dir_list:
        if arg.v is not None and mc_dir != arg.v: continue
        path = "../{}".format(mc_dir)
        for enabled_file in enabled_file_list:
            install = Install(mc_dir, enabled_file, False)
            install.install()

        for disabled_file in disabled_file_list:
            install = Install(mc_dir, disabled_file, True)
            install.install()

        # tomil-w changes something, so it needs to be refreshed
        process = Popen([PACKWIZ, "refresh"], cwd=path, stdout=PIPE, text=True, bufsize=1)
        set_logger(mc_dir, "DEBUG")
        for e in process.stdout:
            text = e.strip()
            logger.info(text)


def remove_mod(mc_ver_list: list[str], mods: list[dict[str, str]]):
    for mc_ver in mc_ver_list:
        set_logger(mc_ver, "DEBUG")
        mc_dir = Path("../{}".format(mc_ver))
        mods_dir = mc_dir.joinpath("mods")
        if not mods_dir.exists():
            continue
        files = [f.name for f in mods_dir.iterdir() if f.is_file()]
        dir_mods = [f.replace(".pw.toml", "") for f in files if re.match(".*\\.pw\\.toml", f)]
        mc_semver = Version(mc_ver)
        for dir_mod in dir_mods:
            should_remove = False
            meta = get_meta(dir_mod, mods)
            if meta:
                condition = NpmSpec(meta.get("version", "*"))
                if not condition.match(mc_semver):
                    should_remove = True
            else:
                should_remove = True
            if should_remove:
                process = Popen(
                    [PACKWIZ, "remove", dir_mod],
                    stdout=PIPE,
                    cwd=mc_dir,
                    text=True,
                    bufsize=1
                )
                for line in process.stdout:
                    logger.info(line.strip())
                process.wait()


def clean_log(mc_ver_list: list[str]):
    for mc_ver in mc_ver_list:
        path = Path("../logs/{}-install.log".format(mc_ver))
        path.unlink(missing_ok=True)


def get_meta(name: str, mod_list: list[dict[str, str]]) -> dict[str, str]:
    for mod in mod_list:
        name_list = [mod.get(MR, ""), mod.get(CF, ""), mod.get(NAME, "").lower()]
        if name in name_list:
            return mod

    return {}


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
    script_dir = Path(__file__).resolve().parent
    os.chdir(script_dir)
    main()