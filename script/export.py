from subprocess import Popen, PIPE
from pathlib import Path
from loguru import logger
from argparse import ArgumentParser
from utils.constant import *

import re
import os
import sys
import shutil
import tomllib
import tomli_w


def main():
    parser = ArgumentParser()
    parser.add_argument('-v')
    arg = parser.parse_args()

    mc_dir_list = [f.name for f in list(Path("../").glob("*/")) if f.joinpath("pack.toml").exists()]
    if (arg.v is not None) and (arg.v not in mc_dir_list): raise ValueError
    is_release = os.getenv("IS_RELEASE", "false")
    run_num = os.getenv("GITHUB_RUN_NUMBER", "1")
    for mc_dir in mc_dir_list:
        if arg.v is not None and mc_dir != arg.v: continue
        logger.remove()
        logger.add(
            sink=sys.stdout,
            format="<green>[{time:HH:mm:ss}]</green> <level>[{level}/(" + mc_dir + ")]</level>: <level>{message}</level>",
            level="DEBUG",
            colorize=True
        )
        remove_side(mc_dir)
        copy_file(mc_dir)
        path = "../{}/pack.toml".format(mc_dir)
        with open(path, "r", encoding="utf-8") as f:
            original = f.read()

        try:
            with open(path, "rb") as f:
                data = tomllib.load(f)
            original_version = data["version"]
            mc_ver = data["versions"]["minecraft"]
            if re.match(".*alpha.*", original_version): raise ValueError
            if is_release == "false":
                original_version = re.sub("-(beta|rc)\\.\\d+", "", original_version)
                data["version"] = original_version + "-alpha.{0}+mc{1}".format(run_num, mc_ver)
            else:
                data["version"] = original_version + "+mc{}".format(mc_ver)
            with open(path, "wb") as f:
                tomli_w.dump(data, f)

            process = Popen(
                [PACKWIZ, "mr", "export"],
                cwd="../{}".format(mc_dir),
                stdout=PIPE,
                text=True,
                bufsize=1
            )
            for line in process.stdout:
                logger.info(line.strip())
            process.wait()
        finally:
            restore_side(mc_dir)
            with open(path, "w", encoding="utf-8") as f:
                f.write(original)
            delete_file(mc_dir)
            process = Popen([PACKWIZ, "refresh"], cwd="../{}".format(mc_dir), stdout=PIPE, text=True, bufsize=1)
            for e in process.stdout:
                text = e.strip()
                logger.info(text)
            process.wait()


def remove_side(mc_dir: str):
    dir_from = "../{}/mods".format(mc_dir)
    dir_to = "../.cache/mods_{}".format(mc_dir)
    shutil.copytree(dir_from, dir_to)
    toml_file_list = [f.name for f in Path(dir_from).iterdir() if f.is_file() and re.match(".*\\.pw\\.toml", f.name)]
    for toml_file in toml_file_list:
        with open(Path(dir_from).joinpath(toml_file), "rb") as f:
            data = tomllib.load(f)
        if "side" in data:
            del data["side"]
            with open(Path(dir_from).joinpath(toml_file), "wb") as f:
                tomli_w.dump(data, f)


def restore_side(mc_dir: str):
    dir_from = "../.cache/mods_{}".format(mc_dir)
    dir_to = "../{}/mods".format(mc_dir)
    shutil.rmtree(dir_to, ignore_errors=True)
    shutil.copytree(dir_from, dir_to)
    shutil.rmtree(dir_from, ignore_errors=True)
    path = Path("../.cache")
    if len(list(path.iterdir())) == 0:
        path.rmdir()


def copy_file(mc_ver: str):
    source = "../internal-files"
    target = "../{}".format(mc_ver)
    shutil.copytree(source, target, dirs_exist_ok=True)


def delete_file(mc_ver: str):
    file_list = [i.name for i in Path("../internal-files").iterdir()]
    for file in file_list:
        path = Path("../{}".format(mc_ver)).joinpath(file)
        if path.is_file():
            path.unlink()
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)


if __name__ == "__main__":
    script_dir = Path(__file__).resolve().parent
    os.chdir(script_dir)
    main()