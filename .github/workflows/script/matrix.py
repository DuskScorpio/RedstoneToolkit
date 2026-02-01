from pathlib import Path

import json
import tomllib


def main():
    mc_dirs = [f.name for f in list(Path("./").glob("*/")) if f.joinpath("pack.toml").exists()]
    mc_vers = []
    dir_map = {}
    ver_map = {}
    for mc_dir in mc_dirs:
        path = "{}/pack.toml".format(mc_dir)
        with open(path, "rb") as f:
            data = tomllib.load(f)
        mc_ver = data["versions"]["minecraft"]
        mc_vers.append(mc_ver)
        dir_map[mc_ver] = mc_dir
        ver_map[mc_ver] = data["version"]

    json_data = {
        "mc_vers": mc_vers,
        "dir_map": dir_map,
        "ver_map": ver_map
    }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(json_data, f)


if __name__ == "__main__":
    main()