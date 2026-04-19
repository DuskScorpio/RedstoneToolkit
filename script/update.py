from script.utils.constant import *
from script.utils import logutil, util
from pathlib import Path
from subprocess import Popen, PIPE, STDOUT

import re
import tomllib
import tomli_w

def run(match: str):
    clean_log()
    for platform in [PlatForm.MODRINTH, PlatForm.CURSEFORGE]:
        dir_vers = util.get_dir_vers(platform)
        for dir_ver in dir_vers:
            if not util.check_match(match, dir_ver):
                continue
            path = Path(platform).joinpath(dir_ver)
            record = Disable(dir_ver, platform)
            record.init()
            with Popen(
                [PACKWIZ, "update", "--all", "--yes"],
                stdout=PIPE,
                stderr=STDOUT,
                cwd=path,
                text=True,
                bufsize=1
            ) as process:
                process_log(process, dir_ver, platform)
                process.wait()
            record.disable()

def process_log(process: Popen[str], version: str, platform: PlatForm):
    name_dict = name_id_dict(version, platform)
    for line in process.stdout:
        text = line.strip()
        log_1 = logutil.Logger(
            f"{version}/{platform}",
            write=True,
            log_name=f"{platform}-{version}-update.log",
            level_f=logutil.Level.WARNING
        ).get_log()
        if re.match("Warning:.*", text):
            log_1.warning(text.replace("Warning: ", ""))
        else:
            log_1.info(text)
        if re.match(".+: .+ -> .+", text):
            match = re.search(".+:", text)
            if match:
                log_2 = logutil.Logger(
                    f"{version}/{platform}",
                    write=True,
                    log_name=f"{platform}-{version}-update.log"
                ).get_log()
                mod_id = name_dict[match.group().strip()[:-1]]
                log_2.info("{} update completed!".format(mod_id))


def name_id_dict(mc_ver: str, platform: PlatForm) -> dict[str, str]:
    path = Path(platform).joinpath(mc_ver).joinpath("mods")
    path.mkdir(parents=True, exist_ok=True)
    files = [f.name for f in path.iterdir() if f.is_file() and re.match(".*\\.pw\\.toml", f.name)]
    name_and_id = {}
    for file in files:
        with open(path.joinpath(file), "rb") as f:
            data = tomllib.load(f)
        name = data[NAME]
        mod_id = file.replace(".pw.toml", "")
        name_and_id[name] = mod_id

    return name_and_id


def clean_log():
    path = Path("logs")
    if path.exists():
        file_path_list = [f for f in path.iterdir() if re.match(".*-update\\.log", f.name)]
        for file_path in file_path_list:
            file_path.unlink()


class Disable:
    __disabled_list = []

    def __init__(self, version: str, platform: PlatForm):
        self.version = version
        self.platform = platform

    def init(self):
        path = Path(self.platform).joinpath(self.version).joinpath("mods")
        if path.exists():
            file_list = [f for f in path.iterdir() if re.match(".*\\.pw\\.toml", f.name)]
            for file in file_list:
                with open(file, "rb") as f:
                    data = tomllib.load(f)
                if re.match(".*\\.disabled", data["filename"]):
                    self.__disabled_list.append(file.name)

    def disable(self):
        log = logutil.Logger("update").get_log()
        for file_name in self.__disabled_list:
            self.__disable(file_name)
        process = Popen(
            [PACKWIZ, "refresh"],
            cwd=Path(self.platform).joinpath(self.version),
            stdout=PIPE,
            text=True,
            bufsize=1
        )
        for e in process.stdout:
            text = e.strip()
            log.info(text)
        process.wait()


    def __disable(self, file_name: str):
        path = Path(self.platform).joinpath(self.version).joinpath("mods").joinpath(file_name)
        if not path.exists():
            return
        with open(path, "rb") as fr:
            data = tomllib.load(fr)
        original_name = data["filename"]
        if re.match(".*\\.disabled", original_name):
            return
        data["filename"] = original_name + ".disabled"
        with open(path, "wb") as fw:
            tomli_w.dump(data, fw)


if __name__ == "__main__":
    print(logutil.Level.WARNING.name)