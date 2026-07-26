import re
import tomllib
from pathlib import Path
from subprocess import Popen, STDOUT, PIPE

import tomli_w

from script.utils import util, logutil
from script.utils.constant import *


def run(match: str):
    for platform_source in PlatformSource:
        mc_dirs = util.get_dir_vers(platform_source)
        for mc_dir in mc_dirs:
            if not util.check_match(match, mc_dir):
                continue
            path = Path(platform_source).joinpath(mc_dir)
            update(path, platform_source, mc_dir)


def update(cwd: Path, platform: PlatformSource, mc_dir: str):
    record = Disabled(platform, mc_dir)
    record.mark()
    with Popen(
        [PACKWIZ, "update", "--all", "--yes"],
        stdout=PIPE,
        stderr=STDOUT,
        cwd=cwd,
        text=True,
        bufsize=1
    ) as popen:
        for e in popen.stdout:
            process_log(e.strip(), platform, mc_dir)
    record.disable()


def process_log(info: str, platform: PlatformSource, mc_dir: str):
    log = logutil.get_log("update")
    prefix = f"({platform}/{mc_dir})"
    log.debug(f"{prefix} {info}")
    if re.match(".+: .+ -> .+", info):
        match = re.search(".+:", info)
        mod_name = match.group()[:-1]
        log.info(f"{prefix} {mod_name} update successful!")
    elif re.match("Failed to check updates for .*", info):
        match = re.search("Failed to check updates for .+:", info)
        mod_name = match.group()[28:-1]
        log.error(f"{prefix} {mod_name} update failed!")


class Disabled:
    def __init__(self, platform: PlatformSource, mc_dir: str):
        self.platform = platform
        self.mc_dir = mc_dir
        self.disabled_list: list[Path] = []
        self.cwd = Path(platform).joinpath(mc_dir)

    def mark(self):
        mods_dir = self.cwd.joinpath("mods")
        if not mods_dir.exists():
            return
        for mod_path in mods_dir.iterdir():
            with mod_path.open("rb") as fr:
                data = tomllib.load(fr)
            filename: str = data["filename"]
            if filename.endswith(".disabled"):
                self.disabled_list.append(mod_path)

    def disable(self):
        for mod_path in self.disabled_list:
            if not mod_path.exists():
                continue
            with mod_path.open("rb") as fr:
                data = tomllib.load(fr)
            filename: str = data["filename"]
            if not filename.endswith(".disabled"):
                data["filename"] = filename + ".disabled"
                with mod_path.open("wb") as fw:
                    tomli_w.dump(data, fw)
        self._refresh()

    def _refresh(self):
        log = logutil.get_log("update")
        with Popen(
            [PACKWIZ, "refresh"],
            stdout=PIPE,
            stderr=STDOUT,
            cwd=self.cwd,
            text=True,
            bufsize=1
        ) as popen:
            for e in popen.stdout:
                log.debug(f"({self.platform}/{self.mc_dir}) {e.strip()}")
