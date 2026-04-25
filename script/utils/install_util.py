from script.utils.constant import *
from script.utils import logutil, util
from subprocess import Popen, PIPE, STDOUT
from enum import StrEnum, auto
from pathlib import Path
from threading import Thread, Event

import re
import tomllib
import tomli_w


class Type(StrEnum):
    MODS = auto()
    RESOURCEPACKS = auto()


class From(StrEnum):
    MODRINTH = auto()
    CURSEFORGE = auto()
    URL = auto()


class Install:
    def __init__(
            self,
            platform: PlatForm,
            mc_dir: str,
            meta: dict,
            disabled: bool,
            file_type: Type
    ):
        self.platform = platform
        self.mc_dir = mc_dir
        self.mod_meta = meta
        self.path = f"./{platform}/{mc_dir}"
        self.disabled = disabled
        self.file_type = file_type
        self.log = logutil.Logger(f"{mc_dir}/{platform}").get_log()
        self.log_w = logutil.Logger(
            name=f"{mc_dir}/{platform}",
            write=True,
            log_name=f"{platform}-{mc_dir}-install.log",
            level_f=logutil.Level.WARNING
        ).get_log()

    def install(self):

        # sb curseforge
        if self.platform == PlatForm.CURSEFORGE:
            cf_condition: str | None = self.mod_meta.get(CF_SKIP)
            if not cf_condition is None and util.check_match(cf_condition, self.mc_dir): return

            urls: dict | None = self.mod_meta.get(URLS)
            if urls is None or self.mc_dir not in urls: return

        if not util.check_match(self.mod_meta.get("version", "*"), self.mc_dir):
            return
        mod_name = self.__install()
        if self.disabled:
            self.__disable(mod_name)
        else:
            self.__enable(mod_name)

    def __install(self) -> str:
        name_list = []

        platform_map = {
            MR: "mr",
            CF: "cf",
            PlatForm.MODRINTH: [MR, CF],
            PlatForm.CURSEFORGE: [CF] # don't let cf download anything from mr
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
            if self.mc_dir in urls:
                self.__url_install(mod_name, urls[self.mc_dir])
                return mod_name.lower()
            name_list.append(mod_name.lower())

        mod_name = name_list[0]
        self.log_w.warning(f"{mod_name} install failed!")
        return mod_name

    def __try_install(self, platform: str, mod_name: str) -> bool:
        args = [PACKWIZ, platform, "add", mod_name]

        # we only need the mod for curseforge
        if platform == "cf":
            args.append("--category")
            match self.file_type:
                case Type.MODS:
                    args.append("mc-mods")
                case Type.RESOURCEPACKS:
                    args.append("texture-packs")
                case _:
                    raise ValueError

        with Popen(
                args,
                cwd=self.path,
                text=True,
                stdout=PIPE,
                stderr=STDOUT,
                stdin=PIPE,
                bufsize=1
        ) as process:
            # Don't change these, because it works by mystical powers
            flag = False
            is_successful = True
            event = Event()
            for e in process.stdout:
                text = e.strip()
                if text == "Dependencies found:" and not flag:
                    flag = True
                    thread = Thread(target=self.__input_thread, args=(process, event,), daemon=True)
                    thread.start()
                if flag:
                    event.set()
                self.log.info(text)
                if re.match("Failed to (add|get file for) project:.*", text) or text == "No projects found!":
                    is_successful = False
            process.wait()
        return is_successful

    @staticmethod
    def __input_thread(popen: Popen, event: Event):
        while True:
            event.wait(timeout=3)
            if not event.is_set():
                popen.stdin.write("n\n")
                popen.stdin.flush()
                break
            else:
                event.clear()

    def __url_install(self, mod_name: str, url: str):
        with Popen(
                [PACKWIZ, "url", "add", mod_name, url],
                cwd=self.path,
                text=True,
                stdout=PIPE,
                stderr=PIPE,
                stdin=PIPE,
                bufsize=1
        ) as process:
            for e in process.stdout:
                text = e.strip()
                self.log.info(text)
            process.wait()

    def __is_installed(self, mod_name: str) -> bool:
        path = Path(self.path).joinpath(self.file_type).joinpath(f"{mod_name}.pw.toml")
        return path.exists()

    def __disable(self, mod_name: str):
        path = Path(self.platform).joinpath(self.mc_dir).joinpath(self.file_type).joinpath(f"{mod_name}.pw.toml")
        if not path.exists():
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
        path = Path(self.platform).joinpath(self.mc_dir).joinpath(self.file_type).joinpath(f"{mod_name}.pw.toml")
        if not Path(path).exists():
            return
        with open(path, "rb") as f:
            data = tomllib.load(f)
        original_name = data["filename"]
        if re.match(".*\\.disabled", original_name):
            data["filename"] = str(original_name).replace(".disabled", "")
            with open(path, "wb") as f:
                tomli_w.dump(data, f)
