from pathlib import Path

import re
import json
import tomllib


CURSEFORGE = "curseforge"
MODRINTH = "modrinth"

def main():
    json_data = {
        MODRINTH:  {
            "mc_vers": [],
            "dir_map": {},
            "type_map": {},
            "ver_map": {}
        },
        CURSEFORGE: {
            "mc_vers": [],
            "dir_map": {},
            "type_map": {},
            "ver_map": {}
        }
    }
    for platform in [MODRINTH, CURSEFORGE]:
        dirs = [f.name for f in Path(platform).iterdir() if f.joinpath("pack.toml").exists()]
        for mc_dir in dirs:
            toml_path = Path(platform).joinpath(mc_dir).joinpath("pack.toml")
            with open(toml_path, "rb") as fr:
                data = tomllib.load(fr)
            mc_ver = data["versions"]["minecraft"]
            pack_ver = data["version"]
            json_data[platform]["mc_vers"].append(mc_ver)
            json_data[platform]["dir_map"][mc_ver] = mc_dir
            if re.match(".*alpha\\.\\d+", pack_ver): raise ValueError
            pack_type = "beta" if re.match(".*(beta|rc)\\.\\d+", pack_ver) else "release"
            json_data[platform]["type_map"][mc_ver] = pack_type
            json_data[platform]["ver_map"][mc_ver] = pack_ver

    with open("matrix_data.json", "w", encoding="utf-8") as fw:
        json.dump(json_data, fw)

if __name__ == "__main__":
    main()