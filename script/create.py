from script.utils.constant import *
from script.utils import util, logutil
from pathlib import Path
from semantic_version import Version
from subprocess import Popen, PIPE

import tomllib
import shutil


def run(versions: list[str], snapshot: bool):
    if versions:
        for version in versions:
            with Create(version=version): ...
    else:
        with Create(snapshot=snapshot): ...


class Create:
    __arg = [
        PACKWIZ, "init",
        "--author", "Scorpio",
        "--modloader", "fabric", "--fabric-latest",
        "--name", "RedstoneToolkit"
    ]

    def __init__(self, version: str = "latest", snapshot: bool = False):
        self.version = version
        self.snapshot = snapshot

    def __enter__(self):
        self.__parser_version()
        log = logutil.Logger("create").get_log()
        path = Path(".cache").joinpath("create")
        path.mkdir(parents=True, exist_ok=True)
        process = Popen(
            self.__arg,
            cwd=path,
            text=True,
            stdout=PIPE,
            stderr=PIPE,
            bufsize=1
        )
        for e in process.stdout:
            log.info(e.strip())
        with open(path.joinpath("pack.toml"), "rb") as f:
            data = tomllib.load(f)
        mc_dir_ver: str = str(Version.coerce(data["versions"]["minecraft"]).truncate())
        for platform in [PlatForm.MODRINTH, PlatForm.CURSEFORGE]:
            copy_path = Path(platform).joinpath(mc_dir_ver)
            if not copy_path.exists():
                shutil.copytree(path, copy_path)


    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        path = Path(".cache").joinpath("create")
        shutil.rmtree(path)
        util.try_remove_empty_cache()
        return True

    def __parser_version(self):
        if self.version == "latest":
            self.__arg.append("--latest")
            if self.snapshot:
                self.__arg.append("--snapshot")
        else:
            self.__arg.extend(["--mc-version", self.version])

        ver_list: list[Version] = []
        for platform in [PlatForm.MODRINTH, PlatForm.CURSEFORGE]:
            dir_vers = util.get_dir_vers(platform)
            for dir_ver in dir_vers:
                path = Path(platform).joinpath(dir_ver).joinpath("pack.toml")
                with open(path, "rb") as f:
                    data = tomllib.load(f)
                ver_list.append(Version(data["version"]))
        max_ver = str(max(ver_list))
        self.__arg.extend(["--version", max_ver])
