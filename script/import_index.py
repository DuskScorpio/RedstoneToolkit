from pathlib import Path
from ruamel.yaml import YAML
from script.utils.constant import *

import re


def main():
    index_dir = Path("../.index")
    if not index_dir.exists() or not index_dir.is_dir():
        return

    files = [f.name for f in index_dir.iterdir() if f.is_file()]
    mod_ids = [f.replace(".pw.toml", "") for f in files if re.match(".*\\.pw\\.toml", f)]
    yaml = YAML()
    yaml.block_seq_indent = 2
    with open(FILE_PATH, "r", encoding="utf-8") as f:
        data = dict(yaml.load(f))

    enabled_mods: list[dict[str, str]] = data.get("enabled_mods", []).copy()
    disabled_mods: list[dict[str, str]] = data.get("disabled_mods", []).copy()
    new_mods = []
    for mod_id in sorted(mod_ids):
        enabled_slugs = [i["mr_slug"] for i in enabled_mods if "mr_slug" in i]
        disabled_slug = [i["mr_slug"] for i in disabled_mods if "mr_slug" in i]
        if mod_id not in enabled_slugs and mod_id not in disabled_slug:
            new_mods.append({"mr_slug": mod_id})
    data["enabled_mods"].extend(new_mods)

    if new_mods:
        comment = data["enabled_mods"]
        comment.yaml_set_comment_before_after_key(enabled_mods.__len__(), "\n======NEW MODS======")

    # save
    with open(FILE_PATH, "w", encoding="utf-8") as f:
        yaml.dump(data, f)


if __name__ == "__main__":
    main()