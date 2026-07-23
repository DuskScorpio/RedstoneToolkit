#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import tomllib
import urllib.request
from pathlib import Path
from typing import Any

from semantic_version import Version

REPO = Path.cwd()
MANIFEST_URL = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
CHANGELOG_SCRIPT = REPO / "script" / "gen_changelog.py"
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


def needs_update(version_id: str | None) -> tuple[bool, str | None, str | None]:
    if not version_id:
        return False, None, None
    version_dir = dir_name(version_id)
    current_version = current_pack_minecraft(version_dir)
    return current_version != version_id, version_dir, current_version


def install_version(version_dir: str) -> dict[str, Any]:
    cmd = [PYTHON, "-m", "script", "install", "--platform", "all", "--match", version_dir]
    print(">>> " + " ".join(cmd), flush=True)
    proc = subprocess.Popen(
        cmd,
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    warn_count = 0
    success_count = 0
    sample_failures: list[str] = []
    assert proc.stdout is not None
    while True:
        line = proc.stdout.readline()
        if line:
            line = line.rstrip("\n")
            print(line, flush=True)
            lower = line.lower()
            if "install failed!" in lower:
                warn_count += 1
                if len(sample_failures) < 8:
                    sample_failures.append(line)
            if "successfully added!" in lower:
                success_count += 1
        ret = proc.poll()
        if ret is not None:
            for rest in proc.stdout.read().splitlines():
                print(rest, flush=True)
                lower = rest.lower()
                if "install failed!" in lower:
                    warn_count += 1
                    if len(sample_failures) < 8:
                        sample_failures.append(rest)
                if "successfully added!" in lower:
                    success_count += 1
            if ret != 0:
                print(f"[WARN] install for {version_dir} exited {ret}; continuing so partial availability is visible", flush=True)
            return {
                "exit_code": ret,
                "warnings": warn_count,
                "added": success_count,
                "sample_failures": sample_failures,
            }
        time.sleep(1)


def regenerate_changelog() -> None:
    env = os.environ.copy()
    env.setdefault("CHANGELOG_REMOTE", "upstream")
    result = run([PYTHON, str(CHANGELOG_SCRIPT)], env=env)
    (REPO / "changelog.md").write_text(result.stdout, encoding="utf-8")


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

    actions: list[tuple[str, str, str, str | None]] = []
    snap_needed, snap_dir, current_snap = needs_update(latest_snap)
    if snap_needed and latest_snap and snap_dir:
        actions.append(("snapshot", latest_snap, snap_dir, current_snap))

    rel_needed, rel_dir, current_rel = needs_update(latest_rel)
    if rel_needed and latest_rel and rel_dir:
        actions.append(("release", latest_rel, rel_dir, current_rel))

    if not actions:
        print("\nSnapshot discover run complete.\n")
        print(f"Latest snapshot: {latest_snap}")
        print(f"Latest release: {latest_rel}\n")
        print("No new Minecraft versions detected.")
        print("No files changed.")
        set_output("changes", "false")
        return

    completed: list[tuple[str, str, str, str | None]] = []
    install_summaries: list[tuple[str, dict[str, object]]] = []

    for kind, version_id, target_dir, previous_version in actions:
        print(f"\n=== Setting up {kind}: {version_id} -> {target_dir} ===", flush=True)
        run([PYTHON, "-m", "script", "remove", "--versions", target_dir])
        if kind == "snapshot":
            run([PYTHON, "-m", "script", "create", "--snapshot"])
        else:
            run([PYTHON, "-m", "script", "create", "--versions", version_id])

        install_summaries.append((target_dir, install_version(target_dir)))
        regenerate_changelog()
        completed.append((kind, version_id, target_dir, previous_version))

    versions = [version_id for _, version_id, _, _ in completed]
    commit_msg = f"Add {versions[0]}" if len(versions) == 1 else f"Add {' and '.join(versions)}"
    changed = git_changed_files()

    print("\nSnapshot discover run complete.\n")
    print("Detected update:")
    for kind, version_id, target_dir, previous_version in completed:
        if previous_version and previous_version != version_id:
            print(f"- {kind}: {previous_version} -> {version_id}")
        else:
            print(f"- {kind}: {version_id}")
        print(f"- target dir: {target_dir}")

    print("\nResult:")
    print("- remove/create: success")
    for target_dir, summary in install_summaries:
        warnings = int(summary["warnings"])
        exit_code = int(summary["exit_code"])
        status = "completed with warnings" if warnings or exit_code else "completed"
        print(f"- install {target_dir}: {status} (exit {exit_code}, failed/unavailable {warnings}, added {summary['added']})")
    print("- changelog: regenerated")
    print(f"- proposed commit: {commit_msg}")
    print(f"- changed files: {len(changed)}\n")
    print("Changed files:")
    for line in changed:
        print(f"- {line}")

    for target_dir, summary in install_summaries:
        sample_failures = summary["sample_failures"]
        if sample_failures:
            print(f"\nSample install failures for {target_dir}:")
            for line in sample_failures:
                print(f"- {line}")

    set_output("changes", "true" if changed else "false")
    set_output("commit_message", commit_msg)
    set_output("versions", ",".join(versions))


if __name__ == "__main__":
    main()
