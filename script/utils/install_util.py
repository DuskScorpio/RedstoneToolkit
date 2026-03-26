from script.utils.constant import *
from script.utils import logutil
from subprocess import Popen, PIPE
from semantic_version import Version, NpmSpec
from pathlib import Path

import re
import tomllib
import tomli_w


class Install:
    def __init__(self, platform: PlatForm, mc_ver: str, meta: dict, disabled: bool):
        self.platform = platform
        self.mc_ver = mc_ver
        self.mod_meta = meta
        self.path = f"./{platform}/{mc_ver}"
        self.disabled = disabled
        self.log = logutil.Logger(f"{mc_ver}/{platform}").get_log()
        self.log_w = logutil.Logger(
            name=f"{mc_ver}/{platform}",
            write=True,
            log_name=f"{platform}-{mc_ver}-install.log",
            level_f=logutil.Level.WARNING
        ).get_log()

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
        # tomil-w changes something, so it needs to be refreshed
        process = Popen([PACKWIZ, "refresh"], cwd=self.path, stdout=PIPE, text=True, bufsize=1)
        log = logutil.Logger(name=f"install/{self.mc_ver}").get_log()
        for e in process.stdout:
            log.info(e.strip())
        process.wait()

    def __install(self) -> str:
        name_list = []

        platform_map = {
            MR: "mr",
            CF: "cf",
            PlatForm.MODRINTH: [MR, CF],
            PlatForm.CURSEFORGE: [CF, MR]
        }
        for i in platform_map.get(self.platform):
            if i in self.mod_meta:
                mod_name = self.mod_meta.get(i)
                if self.__is_installed(mod_name):
                    return mod_name
                successful = self.__try_install(platform_map[i], mod_name)
                if successful:
                    return mod_name
                name_list.append(mod_name)

        if URLS in self.mod_meta:
            mod_name: str = self.mod_meta.get(NAME)
            if self.__is_installed(mod_name.lower()):
                return mod_name.lower()
            urls: dict = self.mod_meta.get(URLS)
            if self.mc_ver in urls:
                self.__url_install(mod_name, urls[self.mc_ver])
                return mod_name.lower()
            name_list.append(mod_name.lower())

        mod_name = name_list[0]
        self.log_w.warning(f"{mod_name} install failed!")
        return mod_name

    def __try_install(self, platform: str, mod_name: str) -> bool:
        args = [PACKWIZ, platform, "add", mod_name]

        # we only need the mod for curseforge
        if platform == "cf":
            args.extend(["--category", "mc-mods"])

        process = Popen(
            args,
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
            self.log.info(text)
            if re.match("Failed to (add|get file for) project:.*", text) or text == "No projects found!":
                is_successful = False
        process.wait()
        return is_successful

    def __url_install(self, mod_name: str, url: str):
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
            self.log.info(text)
        process.wait()


    def __is_installed(self, mod_name: str) -> bool:
        path = Path(self.path).joinpath("mods").joinpath(f"{mod_name}.pw.toml")
        return path.exists()

    def __disable(self, mod_name: str):
        path = f"./{self.platform}/{self.mc_ver}/mods/{mod_name}.pw.toml"
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
        path = f"./{self.platform}/{self.mc_ver}/mods/{mod_name}.pw.toml"
        if not Path(path).exists():
            return
        with open(path, "rb") as f:
            data = tomllib.load(f)
        original_name = data["filename"]
        if re.match(".*\\.disabled", original_name):
            data["filename"] = str(original_name).replace(".disabled", "")
            with open(path, "wb") as f:
                tomli_w.dump(data, f)