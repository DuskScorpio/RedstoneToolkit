from script.utils.constant import *
from script.utils import util, logutil
from script.utils.install_util import Install
from semantic_version import Version, NpmSpec
from subprocess import Popen, PIPE
from ruamel.yaml import YAML
from pathlib import Path


def run(platform: PlatForm, version: str | None):
    log = logutil.Logger("install").get_log()
    platform_list = []
    if platform != PlatForm.ALL:
        platform_list.append(platform)
    else:
        platform_list.extend([PlatForm.MODRINTH, PlatForm.CURSEFORGE])
    for i in platform_list:
        versions = util.get_dir_vers(i)
        if version is None:
            for ver in versions:
                __install(i, ver)
        else:
            if version in versions:
                __install(i, version)
            else:
                log.error("version \"{}\" not found".format(version))


def __install(platform: PlatForm, mc_ver: str):
    yaml = YAML()
    mc_path = "./{0}/{1}".format(platform, mc_ver)
    with open(FILE_PATH, "r", encoding=UTF_8) as f:
        data = yaml.load(f)
    enabled_file_list: list[dict[str, str]] = data[ENABLED]
    disabled_file_list: list[dict[str, str]] = data[DISABLED]
    remove_mod(mc_ver, platform, [*enabled_file_list, *disabled_file_list])
    clean_log(platform, mc_ver)

    for enabled_file in enabled_file_list:
        install = Install(platform, mc_ver, enabled_file, False)
        install.install()

    for disabled_file in disabled_file_list:
        install = Install(platform, mc_ver, disabled_file, True)
        install.install()

    # tomil-w changes something, so it needs to be refreshed
    process = Popen([PACKWIZ, "refresh"], cwd=mc_path, stdout=PIPE, text=True, bufsize=1)
    log = logutil.Logger(name=f"install/{mc_ver}").get_log()
    for e in process.stdout:
        log.info(e.strip())


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
            process = Popen(
                [PACKWIZ, "remove", dir_mod],
                stdout=PIPE,
                cwd=f"./{platform}/{mc_ver}",
                text=True,
                bufsize=1
            )
            for line in process.stdout:
                log.info(line.strip())
            process.wait()


def get_meta(name: str, mod_list: list[dict[str, str]]) -> dict[str, str]:
    for mod in mod_list:
        name_list = [mod.get(MR, ""), mod.get(CF, ""), mod.get(NAME, "").lower()]
        if name in name_list:
            return mod

    return {}


def clean_log(platform: PlatForm, mc_ver: str):
    path = Path(f"./logs/{platform}-{mc_ver}-install.log")
    path.unlink(missing_ok=True)