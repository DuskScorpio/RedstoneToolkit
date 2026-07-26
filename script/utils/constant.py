import platform as platforms
from enum import StrEnum, Enum, auto
from pathlib import Path
from warnings import deprecated

__all__ = [
    "PlatFormLegacy",
    "PlatformSource",
    "PlatformSourceList",
    "PACKWIZ",
    "FILE_PATH",
    "ENABLED",
    "DISABLED",
    "RESOURCE",
    "MR",
    "CF",
    "NAME",
    "URLS",
    "CF_SKIP",
    "UTF_8",
    "COMMAND"
]


@deprecated("will remove")
class PlatFormLegacy(StrEnum):
    MODRINTH = auto()
    CURSEFORGE = auto()
    ALL = auto()


class PlatformSource(StrEnum):
    MODRINTH = auto()
    CURSEFORGE = auto()


class PlatformSourceList(Enum):
    MODRINTH = [PlatformSource.MODRINTH]
    CURSEFORGE = [PlatformSource.CURSEFORGE]
    ALL = [PlatformSource.MODRINTH, PlatformSource.CURSEFORGE]

    @property
    def name(self):
        return super().name.lower()


PACKWIZ = Path("tools").joinpath("packwiz.exe" if platforms.system() == "Windows" else "packwiz").absolute()
FILE_PATH = "file_list.yml"
ENABLED = "enabled_files"
DISABLED = "disabled_files"
RESOURCE = "resource_files"
MR = "mr_slug"
CF = "cf_slug"
NAME = "name"
URLS = "urls"
CF_SKIP = "cf_skip"

UTF_8 = "utf-8"

COMMAND = {
    "stop": None,
    "import": {
        "--platform": {
            PlatformSourceList.MODRINTH.name, PlatformSourceList.CURSEFORGE.name, PlatformSourceList.ALL.name
        }
    },
    "install": (platform_and_version := {
        "--platform": {
            PlatformSourceList.MODRINTH.name: (ver := {"--match": {"": {"--reinstall": None}}}),
            PlatformSourceList.CURSEFORGE.name: ver,
            PlatformSourceList.ALL.name: ver
        },
        "--match": {"": {"--reinstall": None}},
        "--reinstall": None
    }),
    "create": {"--snapshot", "--versions"},
    "remove": {"--versions"},
    "update": {"--match"},
    "export": {
        "--platform": {
            PlatformSourceList.MODRINTH.name: {"--version": None},
            PlatformSourceList.CURSEFORGE.name: {"--version": None},
            PlatformSourceList.ALL.name: {"--version": None}
        },
        "--version": None
    },
    "refresh": None,
    "loader": None,
    "update_version": {
        "--version": None,
        "--match": {"": {"--version": None}},
        "--platform": {
            "modrinth": (ver := {
                "--version": None,
                "--match": {"": {"--version": None}},
            }),
            "curseforge": ver,
            "all": ver
        }
    }
}
