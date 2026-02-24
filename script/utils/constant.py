import os


PACKWIZ = os.path.abspath("tools/packwiz.exe")
FILE_PATH = os.path.abspath("file_list.yml")
ENABLED = "enabled_files"
DISABLED = "disabled_files"
MR = "mr_slug"
CF = "cf_slug"
NAME = "name"
URLS = "urls"
UTF_8 = "utf-8"

COMMAND = {
    "stop": None,
    "import": {"-platform": {"mr", "cf", "all"}}
}
