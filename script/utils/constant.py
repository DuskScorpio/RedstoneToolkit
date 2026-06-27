from enum import StrEnum, auto

import os
import platform


class PlatForm(StrEnum):
    MODRINTH = auto()
    CURSEFORGE = auto()
    ALL = auto()


PACKWIZ_EXE = os.path.abspath("tools/packwiz.exe")
PACKWIZ_LINUX = os.path.abspath("tools/packwiz")
PACKWIZ = PACKWIZ_EXE
if platform.system() == "Linux" and not os.access(PACKWIZ_EXE, os.X_OK):
    PACKWIZ = PACKWIZ_LINUX
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
    "import": {"--platform": {PlatForm.MODRINTH, PlatForm.CURSEFORGE, PlatForm.ALL}},
    "install": (platform_and_version := {
        "--platform": {
            PlatForm.MODRINTH: (ver := {"--match": {"": {"--reinstall": None}}}),
            PlatForm.CURSEFORGE: ver,
            PlatForm.ALL: ver
        },
        "--match": {"": {"--reinstall": None}},
        "--reinstall": None
    }),
    "create": {"--snapshot", "--versions"},
    "remove": {"--versions"},
    "update": {"--match"},
    "export": {
        "--platform": {
            PlatForm.MODRINTH: {"--version": None},
            PlatForm.CURSEFORGE: {"--version": None},
            PlatForm.ALL: {"--version": None}
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
