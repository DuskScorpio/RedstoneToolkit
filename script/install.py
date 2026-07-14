from typing import Any

from script.utils.constant import *
from script.utils import util, logutil
from script.utils.install_util import Type, From, Install
from pathlib import Path
from ruamel.yaml import YAML
from subprocess import Popen, STDOUT, PIPE

import re
import tomllib


def run(input_platform: PlatForm, match: str, reinstall: bool):
    clean_log()
    with open(FILE_PATH, "r", encoding=UTF_8) as f:
        yaml = YAML()
        data = yaml.load(f)
    rate_limit_failures: list[str] = []
    for platform in [PlatForm.MODRINTH, PlatForm.CURSEFORGE] if input_platform == PlatForm.ALL else [input_platform]:
        mc_dirs = util.get_dir_vers(platform)
        for mc_dir in mc_dirs:
            if not util.check_match(match, mc_dir): continue
            remove_file(platform, mc_dir, data, reinstall)
            rate_limited = __install(platform, mc_dir, data)
            if rate_limited:
                rate_limit_failures.extend("{}/{}: {}".format(mc_dir, platform, mod) for mod in sorted(rate_limited))
    if rate_limit_failures:
        log = logutil.Logger("install", write=True, log_name="summary-install.log").get_log()
        for mod in rate_limit_failures:
            log.error("Modrinth 429 left install unchecked for {}".format(mod))
        raise SystemExit(1)


def __install(platform: PlatForm, mc_dir: str, data: dict) -> set[str]:
    rate_limited_mods = set()
    # install enabled_mods
    enabled_mods: list[dict[str, Any]] = data[ENABLED]
    for enabled_mod in enabled_mods:
        install = Install(
            platform=platform,
            mc_dir=mc_dir,
            meta=enabled_mod,
            disabled=False,
            file_type=Type.MODS
        )
        rate_limited_mods |= install.install()

    # install disabled_mods
    disabled_mods: list[dict[str, Any]] = data[DISABLED]
    for disabled_mod in disabled_mods:
        install = Install(
            platform=platform,
            mc_dir=mc_dir,
            meta=disabled_mod,
            disabled=True,
            file_type=Type.MODS
        )
        rate_limited_mods |= install.install()

    # install resourcepacks
    resourcepacks: list[dict[str, Any]] = data[RESOURCE]
    for resourcepack in resourcepacks:
        install = Install(
            platform=platform,
            mc_dir=mc_dir,
            meta=resourcepack,
            disabled=False,
            file_type=Type.RESOURCEPACKS
        )
        rate_limited_mods |= install.install()

    # tomil-w changes something, so it needs to be refreshed
    path = Path(platform).joinpath(mc_dir)
    with Popen([PACKWIZ, "refresh"], cwd=path, stdout=PIPE, stderr=STDOUT, text=True, bufsize=1) as process:
        log = logutil.Logger(name=f"install/{mc_dir}").get_log()
        for e in process.stdout:
            log.info(e.strip())
    return rate_limited_mods


def remove_file(platform: PlatForm, mc_dir: str, data: dict, reinstall: bool):
    log = logutil.Logger(f"install/({platform}/{mc_dir})").get_log()
    run_path = Path(platform).joinpath(mc_dir)
    file_class = {
        Type.MODS: [*data[ENABLED], *data[DISABLED]],
        Type.RESOURCEPACKS: data[RESOURCE]
    }
    for file_type in Type:
        path = run_path.joinpath(file_type)
        if not path.exists(): continue
        remove_ids = [i.name.removesuffix(".pw.toml") for i in path.iterdir() if i.name.endswith(".pw.toml")]
        meta_list = file_class[file_type]
        from_dict = __get_from_dict(path)
        for meta in meta_list:
            for slug in [MR, CF, NAME]:
                name: str | None = meta.get(slug)
                if name is None: continue # If the name doesn't exist, continue it
                if name.lower() not in remove_ids: continue # if the mod is new, continue it

                mod_from: From = from_dict.get(name.lower())

                # sb curseforge
                if platform == PlatForm.CURSEFORGE:
                    if mod_from.value == PlatForm.MODRINTH: continue
                    cf_condition: str | None = meta.get(CF_SKIP)
                    if not cf_condition is None and util.check_match(cf_condition, mc_dir): continue

                match = meta.get("version", "*")
                if not util.check_match(match, mc_dir): continue
                if reinstall and mod_from != platform: continue
                remove_ids.remove(name.lower())
        for remove_name in remove_ids:
            with Popen(
                [PACKWIZ, "remove", remove_name],
                cwd=run_path,
                stdout=PIPE,
                stderr=STDOUT,
                text=True,
                bufsize=1
            ) as process:
                for text in process.stdout:
                    log.info(text.strip())


def __get_from_dict(path: Path) -> dict[str, From]:
    from_dict = dict()
    for e in path.iterdir():
        if not e.name.endswith(".pw.toml"): continue
        name = e.name.removesuffix(".pw.toml")
        with open(e, "rb") as f:
            data = tomllib.load(f)
        if "update" not in data:
            from_dict[name] = From.URL
        elif From.MODRINTH in data["update"]:
            from_dict[name] = From.MODRINTH
        elif From.CURSEFORGE in data["update"]:
            from_dict[name] = From.CURSEFORGE
        else:
            raise ValueError
    return from_dict


def clean_log():
    path = Path("logs")
    if not path.exists(): return
    file_path_list = [f for f in path.iterdir() if re.match(".*-install\\.log", f.name)]
    for file_path in file_path_list:
        file_path.unlink()