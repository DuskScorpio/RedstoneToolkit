from subprocess import Popen, PIPE
from pathlib import Path
from loguru import logger

import os
import sys
import tomllib
import tomli_w


PACKWIZ = "../tools/packwiz"


def main():
    mc_ver_list = [f.name for f in list(Path("../").glob("*/")) if f.joinpath("pack.toml").exists()]
    is_release = os.getenv("IS_RELEASE", "false")
    run_num = os.getenv("GITHUB_RUN_NUMBER", "1")
    for mc_ver in mc_ver_list:
        logger.remove()
        logger.add(
            sink=sys.stdout,
            format="<green>[{time:HH:mm:ss}]</green> <level>[{level}/(" + mc_ver + ")]</level>: <level>{message}</level>",
            level="DEBUG",
            colorize=True
        )
        path = "../{}/pack.toml".format(mc_ver)
        with open(path, "r", encoding="utf-8") as f:
            original = f.read()


        with open(path, "rb") as f:
            data = tomllib.load(f)
        original_version = data["version"]
        if is_release == "false":
            data["version"] = str(original_version) + "-alpha.{0}+mc{1}".format(run_num, mc_ver)
        else:
            data["version"] = str(original_version) + "+mc{}".format(mc_ver)
        with open(path, "wb") as f:
            tomli_w.dump(data, f)

        process = Popen(
            [PACKWIZ, "mr", "export"],
            cwd="../{}".format(mc_ver),
            stdout=PIPE,
            text=True,
            bufsize=1
        )
        for line in process.stdout:
            logger.info(line.strip())
        process.wait()

        if is_release == "false":
            with open(path, "w", encoding="utf-8") as f:
                f.write(original)


if __name__ == "__main__":
    main()