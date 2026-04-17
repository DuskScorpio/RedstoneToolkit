from script.utils.constant import *
from script.utils import util, logutil
from script.utils.install_util import Install
from semantic_version import Version, NpmSpec
from subprocess import Popen, PIPE, STDOUT
from ruamel.yaml import YAML
from pathlib import Path

import re


def run(platform: PlatForm, versions: str | None):
    clean_log()
    platform_dict = {
        PlatForm.ALL: [PlatForm.MODRINTH, PlatForm.CURSEFORGE],
        PlatForm.MODRINTH: [PlatForm.MODRINTH],
        PlatForm.CURSEFORGE: [PlatForm.CURSEFORGE]
    }
    for p in platform_dict[platform]:
        mc_dirs= util.get_dir_vers(p)
        if versions is None:
            for mc_dir in mc_dirs:
                __install(p, mc_dir)
        else:
            input_dirs = [i for i in versions.split(",") if i in mc_dirs]
            for input_dir in input_dirs:
                __install(p, input_dir)



def __install(platform: PlatForm, mc_ver: str):
    yaml = YAML()
    with open(FILE_PATH, "r", encoding=UTF_8) as f:
        data = yaml.load(f)
    enabled_file_list: list[dict[str, str]] = data[ENABLED]
    disabled_file_list: list[dict[str, str]] = data[DISABLED]
    remove_mod(mc_ver, platform, [*enabled_file_list, *disabled_file_list])

    for enabled_file in enabled_file_list:
        install = Install(platform, mc_ver, enabled_file, False)
        install.install()

    for disabled_file in disabled_file_list:
        install = Install(platform, mc_ver, disabled_file, True)
        install.install()


def remove_mod(mc_ver: str, platform: PlatForm, mods: list[dict[str, str]]):
    log = logutil.Logger(name=f"install/{mc_ver}").get_log()
    dir_mods = util.get_dir_mods(platform, mc_ver)
    mc_semver = Version(mc_ver)
    for dir_mod in dir_mods:
        should_remove = False
        meta = get_meta(dir_mod, mods)
        if meta:
            condition = NpmSpec(meta.get("version", "*"))
            if not condition.match(mc_semver):
                should_remove = True
        else:
            should_remove = True
        if should_remove:
            with Popen(
                [PACKWIZ, "remove", dir_mod],
                stdout=PIPE,
                stderr=STDOUT,
                cwd=f"./{platform}/{mc_ver}",
                text=True,
                bufsize=1
            ) as process:
                for line in process.stdout:
                    log.info(line.strip())
                process.wait()


def get_meta(name: str, mod_list: list[dict[str, str]]) -> dict[str, str]:
    for mod in mod_list:
        name_list = [mod.get(MR, ""), mod.get(CF, ""), mod.get(NAME, "").lower()]
        if name in name_list:
            return mod

    return {}


def clean_log():
    path = Path("logs")
    if not path.exists(): return
    file_path_list = [f for f in path.iterdir() if re.match(".*-install\\.log", f.name)]
    for file_path in file_path_list:
        file_path.unlink()