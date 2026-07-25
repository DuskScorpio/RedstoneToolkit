import platform as platforms
from enum import StrEnum, Enum, auto
from pathlib import Path
from warnings import deprecated


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
    "import": {"--platform": {PlatFormLegacy.MODRINTH, PlatFormLegacy.CURSEFORGE, PlatFormLegacy.ALL}},
    "install": (platform_and_version := {
        "--platform": {
            PlatFormLegacy.MODRINTH: (ver := {"--match": {"": {"--reinstall": None}}}),
            PlatFormLegacy.CURSEFORGE: ver,
            PlatFormLegacy.ALL: ver
        },
        "--match": {"": {"--reinstall": None}},
        "--reinstall": None
    }),
    "create": {"--snapshot", "--versions"},
    "remove": {"--versions"},
    "update": {"--match"},
    "export": {
        "--platform": {
            PlatFormLegacy.MODRINTH: {"--version": None},
            PlatFormLegacy.CURSEFORGE: {"--version": None},
            PlatFormLegacy.ALL: {"--version": None}
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
