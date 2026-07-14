#!/usr/bin/env python3
"""
Generate changelog.md content for RedstoneToolkit.

Usage:
    python3 script/gen_changelog.py [BASE_REF]

BASE_REF defaults to the latest origin release/* tag, falling back to bb754d4.
Writes result to stdout.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tomllib
from collections import defaultdict
from pathlib import Path

BASE_DEFAULT = "bb754d4"
REPO = Path.cwd()
PLATFORM = "modrinth"


def run_git(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    ).stdout


def resolve_base(cli_base: str | None = None) -> str:
    if cli_base:
        return cli_base

    remote = os.environ.get("CHANGELOG_REMOTE", "origin")
    tags: list[tuple[str, str]] = []
    for line in run_git("ls-remote", "--tags", remote, "release/*").splitlines():
        sha, ref = line.split()[:2]
        if not ref.endswith("^{}"):
            tags.append((ref.removeprefix("refs/tags/"), sha))

    if not tags:
        return BASE_DEFAULT

    latest_tag, latest_sha = sorted(
        tags,
        key=lambda item: tuple(int(x) for x in re.findall(r"\d+", item[0])),
    )[-1]
    return latest_sha or run_git("rev-list", "-n", "1", latest_tag).strip() or BASE_DEFAULT


def read_pack(path: Path) -> dict:
    with path.open("rb") as f:
        return tomllib.load(f)


def read_pack_from_git(ref: str, rel_path: str) -> dict | None:
    content = run_git("show", f"{ref}:{rel_path}")
    if not content:
        return None
    try:
        return tomllib.loads(content)
    except tomllib.TOMLDecodeError:
        return None


def pack_minecraft_version(path: Path, fallback: str) -> str:
    return str(read_pack(path).get("versions", {}).get("minecraft", fallback))


def version_sort_key(version: str) -> tuple[tuple[int, int | str], ...]:
    parts: list[tuple[int, int | str]] = []
    for piece in re.split(r"([0-9]+)", version):
        if piece:
            parts.append((0, int(piece)) if piece.isdigit() else (1, piece))
    return tuple(parts)


def current_folders_and_versions() -> tuple[list[str], dict[str, str]]:
    folders: list[str] = []
    mc_versions: dict[str, str] = {}
    for folder_dir in (REPO / PLATFORM).iterdir():
        pack = folder_dir / "pack.toml"
        if folder_dir.is_dir() and pack.exists():
            folders.append(folder_dir.name)
            mc_versions[folder_dir.name] = pack_minecraft_version(pack, folder_dir.name)
    folders.sort(key=lambda folder: version_sort_key(mc_versions[folder]))
    return folders, mc_versions


def base_folders_and_versions(base: str) -> dict[str, str]:
    mc_versions: dict[str, str] = {}
    for rel in run_git("ls-tree", "-r", "--name-only", base, PLATFORM).splitlines():
        parts = Path(rel).parts
        if len(parts) != 3:
            continue
        _, folder, filename = parts
        if filename != "pack.toml":
            continue
        pack = read_pack_from_git(base, rel)
        if pack:
            mc_versions[folder] = str(pack.get("versions", {}).get("minecraft", folder))
    return mc_versions


def mod_name_from_file(path: Path) -> str | None:
    try:
        text = path.read_text()
    except OSError:
        return None
    match = re.search(r'^name = "(.*)"', text, re.MULTILINE)
    return match.group(1) if match else None


def resolve_mod_name(slug: str, folders: list[str]) -> str:
    for folder in folders:
        name = mod_name_from_file(REPO / PLATFORM / folder / "mods" / f"{slug}.pw.toml")
        if name:
            return name
    return slug.replace("-", " ").replace("_", " ").title()


def main() -> None:
    base = resolve_base(sys.argv[1] if len(sys.argv) > 1 else None)
    folders, current_mc_versions = current_folders_and_versions()
    base_mc_versions = base_folders_and_versions(base)
    folder_order = {folder: i for i, folder in enumerate(folders)}

    news_added: list[str] = []
    news_folders: set[str] = set()
    for folder in folders:
        current_mc = current_mc_versions[folder]
        base_mc = base_mc_versions.get(folder)
        if base_mc is None or base_mc != current_mc:
            news_added.append(f"- Added {current_mc}")
            news_folders.add(folder)

    changes_removed = [
        f"- Removed {base_mc_versions[folder]}"
        for folder in sorted(base_mc_versions, key=lambda f: version_sort_key(base_mc_versions[f]))
        if folder not in current_mc_versions
    ]

    mod_versions: dict[str, set[str]] = defaultdict(set)
    changed_paths = run_git(
        "diff",
        "--name-only",
        "--diff-filter=ACMR",
        base,
        "--",
        f"{PLATFORM}/*/mods/*.pw.toml",
    ).splitlines()
    for rel in changed_paths:
        path = REPO / rel
        parts = Path(rel).parts
        if len(parts) != 4:
            continue
        _, folder, mods_dir, filename = parts
        if (
            path.exists()
            and mods_dir == "mods"
            and filename.endswith(".pw.toml")
            and folder in folder_order
            and folder not in news_folders
        ):
            mod_versions[filename.removesuffix(".pw.toml")].add(folder)

    updates: dict[tuple[int, int], list[str]] = defaultdict(list)
    for slug, version_folders in mod_versions.items():
        indices = [folder_order[folder] for folder in version_folders]
        updates[(min(indices), max(indices))].append(slug)

    out = ["## News", ""]
    out.extend(news_added)
    out += ["", "## Changes", ""]
    out.extend(changes_removed)
    out += ["", "## Updates", ""]

    for start, end in sorted(updates, key=lambda key: (-(key[1] - key[0] + 1), key[0], key[1])):
        range_folders = folders[start : end + 1]
        start_mc = current_mc_versions[range_folders[0]]
        end_mc = current_mc_versions[range_folders[-1]]
        label = f"{start_mc}-{end_mc}:" if start_mc != end_mc else f"{start_mc}:"
        out.append(f"- {label}")
        for slug in sorted(updates[(start, end)], key=lambda s: resolve_mod_name(s, range_folders).lower()):
            out.append(f"  - {resolve_mod_name(slug, range_folders)}")

    print("\n".join(out))


if __name__ == "__main__":
    main()
