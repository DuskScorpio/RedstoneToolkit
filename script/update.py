from subprocess import Popen, PIPE
from pathlib import Path
from loguru import logger
from utils.constant import *

import re
import os
import sys
import tomllib


def main():
    mc_ver_list = [f.name for f in list(Path("../").glob("*/")) if f.joinpath("pack.toml").exists()]
    clean_log(mc_ver_list)
    for mc_ver in mc_ver_list:
        path = "../{}".format(mc_ver)
        process = Popen(
            [PACKWIZ, "update", "--all", "--yes"],
            stdout=PIPE,
            cwd=path,
            text=True,
            bufsize=1
        )
        process_log(process, mc_ver)
        process.wait()


def process_log(process: Popen, mc_ver: str):
    name_dict = name_id_dict(mc_ver)
    for line in process.stdout:
        set_write_logger(mc_ver, "DEBUG", "WARNING")
        text = line.strip()
        if re.match("Warning:.*", text):
            logger.warning(text.replace("Warning: ", ""))
        else:
            logger.info(text)
        logger.remove()
        if re.match(".+: .+ -> .+", text):
            match = re.search(".+:", text)
            if match:
                mod_id = name_dict[match.group().strip()[:-1]]
                set_write_logger(mc_ver ,"DEBUG", "DEBUG")
                logger.info("{} update completed!".format(mod_id))
                logger.remove()


def clean_log(mc_ver_list: list[str]):
    for mc_ver in mc_ver_list:
        path = Path("../logs/{}-update.log".format(mc_ver))
        path.unlink(missing_ok=True)


def name_id_dict(mc_ver: str) -> dict[str, str]:
    path = Path("../{}/mods".format(mc_ver))
    files = [f.name for f in path.iterdir() if f.is_file() and re.match(".*\\.pw\\.toml", f.name)]
    name_and_id = {}
    for file in files:
        with open(path.joinpath(file), "rb") as f:
            data = tomllib.load(f)
        name = data["name"]
        mod_id = file.replace(".pw.toml", "")
        name_and_id[name] = mod_id

    return name_and_id


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
        sink="../logs/{}-update.log".format(mc_ver),
        format="[{time:HH:mm:ss}] [{level}/(" + mc_ver + ")]: {message}",
        level=level_file
    )


if __name__ == "__main__":
    script_dir = Path(__file__).resolve().parent
    os.chdir(script_dir)
    main()