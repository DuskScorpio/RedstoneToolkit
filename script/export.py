import re
import shutil
import tomllib
from pathlib import Path
from subprocess import Popen, PIPE, STDOUT
from tempfile import TemporaryDirectory

import tomli_w

from script.utils import logutil, util
from script.utils.constant import *


def run(version: str | None, platform: PlatForm):
    platform_map = {
        PlatForm.ALL: [PlatForm.MODRINTH, PlatForm.CURSEFORGE],
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
        self._version = version
        self._platform = platform
        self._path = Path(platform).joinpath(version)
        self._temp = TemporaryDirectory(dir=Path())
        self._temp_path = Path(self._temp.name)
        if not self._path.exists():
            assert FileNotFoundError

    def export(self):
        shutil.copytree(self._path, self._temp_path, dirs_exist_ok=True)

        shutil.copytree(Path("internal-files"), self._path, dirs_exist_ok=True)
        self.__write_version()
        self.__override_side()
        self.__refresh()

        self.__export()
        self.__move_file()

    def __export(self):
        log = logutil.Logger(f"{self._platform}/{self._version}").get_log()
        with Popen(
                [PACKWIZ, self._platform, "export"],
                cwd=self._path,
                stdout=PIPE,
                stderr=STDOUT,
                text=True,
                bufsize=1
        ) as process:
            for e in process.stdout:
                log.info(e.strip())

    def __refresh(self):
        log = logutil.Logger(f"{self._platform}/{self._version}").get_log()
        with Popen(
                [PACKWIZ, "refresh"],
                cwd=self._path,
                stdout=PIPE,
                stderr=STDOUT,
                text=True,
                bufsize=1
        ) as process:
            for e in process.stdout:
                log.info(e.strip())

    def __write_version(self):
        path = self._path.joinpath("pack.toml")
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
        path = self._path.joinpath("mods")
        files_path = [f for f in path.iterdir() if f.is_file() and re.match(".*\\.pw\\.toml", f.name)]
        for file_path in files_path:
            with open(file_path, "rb") as fr:
                data = tomllib.load(fr)
            data["side"] = "both"
            with open(file_path, "wb") as fw:
                tomli_w.dump(data, fw)

    def __move_file(self):
        with open(self._path.joinpath("pack.toml"), "rb") as f:
            data = tomllib.load(f)
        name = str(data["name"])
        version = str(data["version"])
        end = "mrpack" if self._platform == PlatForm.MODRINTH else "zip"
        pack_name = f"{name}-{version}.{end}"

        path = self._path.joinpath(pack_name)
        export_path = Path("export").joinpath(pack_name)
        export_path.parent.mkdir(exist_ok=True)
        shutil.move(path, export_path)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        shutil.rmtree(self._path)
        shutil.copytree(self._temp_path, self._path)
        self._temp.__exit__(exc_type, exc_val, exc_tb)
