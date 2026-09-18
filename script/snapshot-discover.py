#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import tomllib
import urllib.request
from pathlib import Path
from typing import Any

from semantic_version import Version

REPO = Path.cwd()
MANIFEST_URL = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
PYTHON = sys.executable


def set_output(name: str, value: str) -> None:
    output_path = os.environ.get("GITHUB_OUTPUT")
    if output_path:
        with open(output_path, "a", encoding="utf-8") as f:
            print(f"{name}={value}", file=f)


def run(cmd: list[str], *, check: bool = True, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    print(">>> " + " ".join(cmd), flush=True)
    result = subprocess.run(
        cmd,
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
    )
    if result.stdout:
        print(result.stdout, end="" if result.stdout.endswith("\n") else "\n", flush=True)
    if check and result.returncode != 0:
        raise SystemExit(result.returncode)
    return result


def fetch_manifest() -> tuple[str | None, str | None]:
    print(f">>> fetch {MANIFEST_URL}", flush=True)
    req = urllib.request.Request(MANIFEST_URL, headers={"User-Agent": "RedstoneToolkit-snapshot-discover/1.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        data = json.load(response)
    snapshots = [v["id"] for v in data["versions"] if v.get("type") == "snapshot"]
    releases = [v["id"] for v in data["versions"] if v.get("type") == "release"]
    return snapshots[0] if snapshots else None, releases[0] if releases else None


def dir_name(version_id: str) -> str:
    base = version_id.split("-")[0]
    return str(Version.coerce(base).truncate())


def current_pack_minecraft(version_dir: str) -> str | None:
    pack = REPO / "modrinth" / version_dir / "pack.toml"
    if not pack.exists():
        return None
    try:
        with pack.open("rb") as f:
            data = tomllib.load(f)
        return data.get("versions", {}).get("minecraft")
    except Exception as exc:
        print(f"[WARN] failed reading {pack}: {exc}", flush=True)
        return None


def needs_update(version_id: str | None, latest_release: str | None = None) -> tuple[bool, str | None, str | None]:
    if not version_id:
        return False, None, None
    version_dir = dir_name(version_id)
    version_path = REPO / "modrinth" / version_dir
    if not version_path.exists():
        return True, version_dir, None
    current = current_pack_minecraft(version_dir)
    if current == version_id:
        return False, None, None
    # If the directory has the latest release, skip snapshot/rc versions that map to the same dir
    if latest_release and current == latest_release and dir_name(latest_release) == version_dir:
        return False, None, None
    return True, version_dir, current



def git_changed_files() -> list[str]:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=True,
    )
    return [line for line in result.stdout.splitlines() if line.strip()]


def main() -> None:
    latest_snap, latest_rel = fetch_manifest()
    print(f"Latest snapshot: {latest_snap}", flush=True)
    print(f"Latest release: {latest_rel}", flush=True)

    # Collect actions keyed by target directory; release overwrites snapshot
    actions: dict[str, tuple[str, str, str | None]] = {}
    snap_needed, snap_dir, current_snap = needs_update(latest_snap, latest_rel)
    if snap_needed and latest_snap and snap_dir:
        actions[snap_dir] = ("snapshot", latest_snap, current_snap)

    rel_needed, rel_dir, current_rel = needs_update(latest_rel, latest_rel)
    if rel_needed and latest_rel and rel_dir:
        actions[rel_dir] = ("release", latest_rel, current_rel)

    if not actions:
        print("\nSnapshot discover run complete.\n")
        print(f"Latest snapshot: {latest_snap}")
        print(f"Latest release: {latest_rel}\n")
        print("No new Minecraft versions detected.")
        print("No files changed.")
        set_output("changes", "false")
        return

    for target_dir, (kind, version_id, previous_version) in actions.items():
        print(f"\n=== Setting up {kind}: {version_id} -> {target_dir} ===", flush=True)
        run([PYTHON, "-m", "script", "remove", "--versions", target_dir])
        if kind == "snapshot":
            run([PYTHON, "-m", "script", "create", "--snapshot"])
        else:
            run([PYTHON, "-m", "script", "create", "--versions", version_id])

    versions = [v for _, v, _ in actions.values()]
    commit_msg = f"Add {versions[0]}" if len(versions) == 1 else f"Add {' and '.join(versions)}"
    changed = git_changed_files()

    print("\nSnapshot discover run complete.\n")
    print("Detected update:")
    for target_dir, (kind, version_id, previous_version) in actions.items():
        if previous_version and previous_version != version_id:
            print(f"- {kind}: {previous_version} -> {version_id}")
        else:
            print(f"- {kind}: {version_id}")
        print(f"- target dir: {target_dir}")

    print("\nResult:")
    print("- remove/create: success")
    print(f"- proposed commit: {commit_msg}")
    print(f"- changed files: {len(changed)}\n")
    print("Changed files:")
    for line in changed:
        print(f"- {line}")

    set_output("changes", "true" if changed else "false")
    set_output("commit_message", commit_msg)
    set_output("versions", ",".join(versions))


if __name__ == "__main__":
    main()
