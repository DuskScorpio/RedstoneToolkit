from pathlib import Path
from loguru import logger
from subprocess import Popen, PIPE
from semantic_version import Version, NpmSpec
from script.utils.constant import *

import re
import sys
import tomllib
import tomli_w


class Install:
    def __init__(self, mc_ver: str, meta: dict, disabled: bool):
        self.mc_ver = mc_ver
        self.mod_meta = meta
        self.path = "../{}".format(mc_ver)
        self.disabled = disabled


    def install(self):
        mc_semver = Version(self.mc_ver)
        condition = NpmSpec(self.mod_meta.get("version", "*"))
        if not condition.match(mc_semver):
            return
        mod_name = self.__install()
        if self.disabled:
            self.__disable(mod_name)
        else:
            self.__enable(mod_name)


    def __install(self) -> str:
        name_list = []
        if MR in self.mod_meta:
            mod_name = self.mod_meta.get(MR)
            if self.__is_installed(mod_name):
                return mod_name
            successful = self.__try_install("mr", mod_name)
            if successful:
                return mod_name
            name_list.append(mod_name)

        if CF in self.mod_meta:
            mod_name = self.mod_meta.get(CF)
            if self.__is_installed(mod_name):
                return mod_name
            successful = self.__try_install("cf", mod_name)
            if successful:
                return mod_name
            name_list.append(mod_name)

        if URLS in self.mod_meta:
            mod_name = self.mod_meta.get(NAME)
            if self.__is_installed(mod_name):
                return mod_name
            urls: dict = self.mod_meta.get(URLS)
            if self.mc_ver in urls:
                self.__url_install(mod_name, urls[self.mc_ver])
                return mod_name
            name_list.append(mod_name)

        mod_name = name_list[0]
        set_write_logger(self.mc_ver, "DEBUG", "WARNING")
        logger.warning("{} install failed!".format(mod_name))
        return mod_name


    def __is_installed(self, mod_name) -> bool:
        path = Path(self.path).joinpath("mods/{}.pw.toml".format(mod_name))
        return path.exists()


    def __url_install(self, mod_name: str, url: str):
        set_logger(self.mc_ver, "DEBUG")
        process = Popen(
            [PACKWIZ, "url", "add", mod_name, url],
            cwd=self.path,
            text=True,
            stdout=PIPE,
            stderr=PIPE,
            stdin=PIPE,
            bufsize=1
        )
        for e in process.stdout:
            text = e.strip()
            logger.info(text)

    def __try_install(self, platform: str, mod_name: str) -> bool:
        set_logger(self.mc_ver, "DEBUG")
        process = Popen(
            [PACKWIZ, platform, "add", mod_name],
            cwd=self.path,
            text=True,
            stdout=PIPE,
            stderr=PIPE,
            stdin=PIPE,
            bufsize=1
        )

        # Don't change these, because it works by mystical powers
        flag = False
        is_successful = True
        for e in process.stdout:
            text = e.strip()
            if text == "Dependencies found:":
                flag = True
            if flag:
                process.stdin.write("n\n")
                process.stdin.flush()
            logger.info(text)
            if re.match("Failed to add project:.*", text):
                is_successful = False
        process.wait()
        return is_successful

    def __disable(self, mod_name: str):
        path = "../{0}/mods/{1}.pw.toml".format(self.mc_ver, mod_name)
        if not Path(path).exists():
            return
        with open(path, "rb") as f:
            data = tomllib.load(f)
        original_name = data["filename"]
        if re.match(".*\\.disabled", original_name):
            return
        data["filename"] = original_name + ".disabled"
        with open(path, "wb") as f:
            tomli_w.dump(data, f)

    def __enable(self, mod_name):
        path = "../{0}/mods/{1}.pw.toml".format(self.mc_ver, mod_name)
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
