from pathlib import Path

import os
import json
import tomllib

def main():
    platform = os.getenv("PLATFORM")
    path = Path(platform).joinpath(os.getenv("dir")).joinpath("pack.toml")
    assets = json.loads("[]" if os.getenv("assets", "") == "" else os.getenv("assets"))
    files_name = [str(i["name"]) for i in assets]
    with open(path, "rb") as fr:
        data = tomllib.load(fr)
    pack_name = "{0}-{1}+mc{2}.{3}".format(
        data["name"],
        data["version"],
        data["versions"]["minecraft"],
        "mrpack" if platform == "modrinth" else "zip"
    )
    with open("publish_data.json", "w", encoding="utf-8") as fw:
        json.dump({"publish": pack_name not in files_name}, fw)


if __name__ == "__main__":
    main()