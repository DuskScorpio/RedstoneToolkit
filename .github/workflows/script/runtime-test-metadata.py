from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path


def java_version(minecraft_version: str) -> int:
    if minecraft_version.startswith("26."):
        return 25

    match = re.match(r"^(\d+)\.(\d+)(?:\.(\d+))?", minecraft_version)
    if match is None:
        raise ValueError(f"Cannot determine Java version for Minecraft {minecraft_version}")

    major = int(match.group(1))
    minor = int(match.group(2))
    patch = int(match.group(3) or 0)

    if (major, minor) >= (1, 21) or (major, minor, patch) >= (1, 20, 5):
        return 21
    if (major, minor) >= (1, 18):
        return 17
    if (major, minor) == (1, 17):
        return 16
    return 8


def read_pack_metadata(pack_path: Path) -> dict[str, str | int]:
    with pack_path.open("rb") as pack_file:
        pack = tomllib.load(pack_file)

    minecraft_version = str(pack["versions"]["minecraft"])
    return {
        "minecraft_version": minecraft_version,
        "java_version": java_version(minecraft_version),
    }


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: runtime-test-metadata.py <pack.toml>")

    metadata = read_pack_metadata(Path(sys.argv[1]))
    print(f"minecraft_version={metadata['minecraft_version']}")
    print(f"java_version={metadata['java_version']}")


if __name__ == "__main__":
    main()
