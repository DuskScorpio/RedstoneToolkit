from enum import StrEnum

import os


class PlatForm(StrEnum):
    MODRINTH = "modrinth"
    CURSEFORGE = "curseforge"
    ALL = "all"


PACKWIZ = os.path.abspath("tools/packwiz.exe")
FILE_PATH = "file_list.yml"
ENABLED = "enabled_files"
DISABLED = "disabled_files"
MR = "mr_slug"
CF = "cf_slug"
NAME = "name"
URLS = "urls"

UTF_8 = "utf-8"

COMMAND = {
    "stop": None,
    "import": {"--platform": {PlatForm.MODRINTH, PlatForm.CURSEFORGE, PlatForm.ALL}},
    "install": (platform_and_version := {
        "--platform": {
            PlatForm.MODRINTH: (ver := {"--version": None}),
            PlatForm.CURSEFORGE: ver,
            PlatForm.ALL: ver
        },
        "--version": None
    }),
    "create": {"--snapshot", "--versions"},
    "remove": {"--versions"},
    "update": {"--version"},
    "export": platform_and_version
}
