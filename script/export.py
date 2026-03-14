from script.utils.constant import *
from script.utils import logutil, util
from subprocess import Popen, PIPE
from pathlib import Path

import os
import re
import shutil
import tomllib
import tomli_w

def run(version: str | None, platform: PlatForm):
    platform_map = {
        PlatForm.ALL: [PlatForm.MODRINTH , PlatForm.CURSEFORGE],
        PlatForm.MODRINTH: [PlatForm.MODRINTH],
        PlatForm.CURSEFORGE: [PlatForm.CURSEFORGE]
    }
    for p in platform_map[platform]:
        if version is None:
            versions = util.get_dir_vers(p)
            for dir_ver in versions:
                with Export(dir_ver, p) as e:
                    e.export()
        else:
            with Export(version, p) as e:
                e.export()


class Export:
    def __init__(self, version: str, platform: PlatForm):
        self.version = version
        self.platform = platform
        self.path = Path(platform).joinpath(version)
        if not self.path.exists():
            assert FileNotFoundError

    def export(self):
        cache_path = Path(".cache").joinpath(self.platform).joinpath(self.version)
        shutil.copytree(self.path, cache_path)

        shutil.copytree(Path("internal-files"), self.path, dirs_exist_ok=True)
        self.__write_version()
        self.__override_side()
        self.__refresh()

        self.__export()
        self.__move_file()

    def __export(self):
        log = logutil.Logger(f"{self.platform}/{self.version}").get_log()
        process = Popen(
            [PACKWIZ, self.platform, "export"],
            cwd=self.path,
            stdout=PIPE,
            stderr=PIPE,
            stdin=PIPE,
            text=True,
            bufsize=1
        )
        for e in process.stdout:
            log.info(e.strip())
        process.wait()

    def __refresh(self):
        log = logutil.Logger(f"{self.platform}/{self.version}").get_log()
        process = Popen(
            [PACKWIZ, "refresh"],
            cwd=self.path,
            stdout=PIPE,
            stderr=PIPE,
            stdin=PIPE,
            text=True,
            bufsize=1
        )
        for e in process.stdout:
            log.info(e.strip())
        process.wait()

    def __write_version(self):
        path = self.path.joinpath("pack.toml")
        is_release = os.getenv("IS_RELEASE", "false")
        run_num = os.getenv("GITHUB_RUN_NUMBER", "1")
        with open(path, "rb") as fr:
            data = tomllib.load(fr)
        original_version = data["version"]
        mc_version = data["versions"]["minecraft"]
        if re.match(".*alpha.*", original_version): raise ValueError
        if is_release == "false":
            original_version = re.sub("-(beta|rc)\\.\\d+", "", original_version)
            data["version"] = original_version + "-alpha.{0}+mc{1}".format(run_num, mc_version)
        else:
            data["version"] = original_version + "+mc{}".format(mc_version)
        with open(path, "wb") as fw:
            tomli_w.dump(data, fw)

    def __override_side(self):
        """Some mods don't mark the side correctly, and the temporary workaround is to override all mods' sides as both"""
        path = self.path.joinpath("mods")
        files_path = [f for f in path.iterdir() if f.is_file() and re.match(".*\\.pw\\.toml", f.name)]
        for file_path in files_path:
            with open(file_path, "rb") as fr:
                data = tomllib.load(fr)
            data["side"] = "both"
            with open(file_path, "wb") as fw:
                tomli_w.dump(data, fw)


    def __move_file(self):
        with open(self.path.joinpath("pack.toml"), "rb") as f:
            data = tomllib.load(f)
        name = str(data["name"])
        version = str(data["version"])
        end = "mrpack" if self.platform == PlatForm.MODRINTH else "zip"
        pack_name = f"{name}-{version}.{end}"

        path = self.path.joinpath(pack_name)
        export_path = Path("export").joinpath(pack_name)
        export_path.parent.mkdir(exist_ok=True)
        shutil.move(path, export_path)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        cache_path = Path(".cache").joinpath(self.platform).joinpath(self.version)
        shutil.rmtree(self.path)
        shutil.copytree(cache_path, self.path)
        shutil.rmtree(cache_path)
        if not any(cache_path.parent.iterdir()):
            cache_path.parent.rmdir()
        util.try_remove_empty_cache()
        return True