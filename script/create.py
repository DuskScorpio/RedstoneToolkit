import shutil
import tomllib
from pathlib import Path
from subprocess import Popen, STDOUT, PIPE
from tempfile import TemporaryDirectory

from semantic_version import Version

from script.utils import util, logutil
from script.utils.constant import *


def run(versions: list[str], snapshot: bool):
    if versions:
        for version in versions:
            with Create(version=version) as c:
                c.create()
    else:
        with Create(snapshot=snapshot) as c:
            c.create()


class Create:
    _arg = [
        PACKWIZ, "init",
        "--author", "Scorpio",
        "--modloader", "fabric", "--fabric-latest",
        "--name", "RedstoneToolkit"
    ]

    def __init__(self, version: str = "latest", snapshot: bool = False):
        self._version = version
        self._snapshot = snapshot
        self._temp = TemporaryDirectory(dir=Path())
        self._temp_path = Path(self._temp.name)
        self._log = logutil.get_log("create", False)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._temp.__exit__(exc_type, exc_val, exc_tb)

    def create(self):
        self._parser_version()
        with Popen(
                self._arg,
                cwd=self._temp_path,
                text=True,
                stdout=PIPE,
                stderr=STDOUT,
                bufsize=1
        ) as popen:
            for e in popen.stdout:
                self._log.info(e.strip())
        with self._temp_path.joinpath("pack.toml").open("rb") as f:
            data = tomllib.load(f)
        mc_dir_ver: str = str(Version.coerce(data["versions"]["minecraft"]).truncate())
        for platform in [PlatFormLegacy.MODRINTH, PlatFormLegacy.CURSEFORGE]:
            copy_path = Path(platform).joinpath(mc_dir_ver)
            if not copy_path.exists():
                shutil.copytree(self._temp_path, copy_path)

    def _parser_version(self):
        if self._version == "latest":
            self._arg.append("--latest")
            if self._snapshot:
                self._arg.append("--snapshot")
        else:
            self._arg.extend(["--mc-version", self._version])

        ver_list: list[Version] = list()
        for platform in [PlatFormLegacy.MODRINTH, PlatFormLegacy.CURSEFORGE]:
            dir_vers = util.get_dir_vers(platform)
            for dir_ver in dir_vers:
                path = Path(platform).joinpath(dir_ver).joinpath("pack.toml")
                with path.open("rb") as f:
                    data = tomllib.load(f)
                ver_list.append(data["version"])
        max_ver = str(max(ver_list)) if ver_list else "0.1.0"
        self._arg.extend(["--version", max_ver])
