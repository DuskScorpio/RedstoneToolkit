from pathlib import Path
from ruamel.yaml import YAML
from script.utils.constant import *

import re


INDEX_DIR = Path(".index")

def run(platform: str = "mr"):
    if platform != "all":
        __import_index(platform)
    else:
        for i in ["mr", "cf"]:
            __import_index(i)


def __import_index(platform: str = "mr"):
    if not INDEX_DIR.exists() or not INDEX_DIR.is_dir(): return
    yaml = YAML()
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.preserve_quotes = True
    if platform == "mr":
        now_slug = MR
        other_slug = CF
    else:
        now_slug = CF
        other_slug = MR

    with open(FILE_PATH, "r", encoding=UTF_8) as f:
        data = yaml.load(f)
    mod_ids = __get_ids()
    enabled_mods: list[dict[str, str]] = data.get(ENABLED, []).copy()
    disabled_mods: list[dict[str, str]] = data.get(DISABLED, []).copy()
    new_mods = []
    for mod_id in sorted(mod_ids):
        enabled_slugs = [i[now_slug] for i in enabled_mods if now_slug in i]
        disabled_slug = [i[now_slug] for i in disabled_mods if now_slug in i]
        if mod_id not in enabled_slugs and mod_id not in disabled_slug:
            new_mods.append(mod_id)

    # merge existing projects
    new_mods_merge = new_mods.copy()
    for status in [ENABLED, DISABLED]:
        for meta in data[status]:
            if other_slug in meta and meta[other_slug] in new_mods_merge:
                meta[now_slug] = meta[other_slug]
                new_mods_merge.remove(meta[other_slug])

    if new_mods_merge:
        mods_list = data[ENABLED]
        mods_list.yaml_set_comment_before_after_key(enabled_mods.__len__(), "\n======NEW MODS======")
        mods_list.extend([{now_slug: i} for i in new_mods_merge])

    with open(FILE_PATH, "w", encoding=UTF_8) as f:
        yaml.dump(data, f)


def __get_ids() -> list[str]:
    files = [f.name for f in INDEX_DIR.iterdir() if f.is_file()]
    return [f.replace(".pw.toml", "") for f in files if re.match(".*\\.pw\\.toml", f)]
