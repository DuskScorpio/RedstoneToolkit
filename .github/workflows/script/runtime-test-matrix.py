from __future__ import annotations

import importlib.util
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from types import ModuleType
from typing import Any


DEFAULT_RUNTIME_TEST_FALLBACK_VERSION = "4.4.0"
JAVA_MINIMUM_RULES = (
    ("26.0.0", 25),
    ("1.19.4", 21),
    ("1.16.5", 17),
)
MOCK_ARTIFACT_CHECK_MODES = {
    "runtime",
    "mock-runtime",
    "boot",
    "mock-boot",
    "offline",
    "mock",
}


def load_metadata_module() -> ModuleType:
    metadata_path = Path(__file__).with_name("runtime-test-metadata.py")
    spec = importlib.util.spec_from_file_location("runtime_test_metadata", metadata_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load metadata script from {metadata_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def natural_key(value: str) -> list[int | str]:
    return [
        int(part) if part.isdigit() else part
        for part in re.split(r"(\d+)", value)
        if part
    ]


def discover_pack_dirs(modrinth_dir: Path) -> list[Path]:
    return sorted(
        (path.parent for path in modrinth_dir.glob("*/pack.toml")),
        key=lambda path: natural_key(path.name),
    )


def parse_pack_version(value: str) -> tuple[int, ...]:
    if not re.fullmatch(r"\d+(?:\.\d+)*", value):
        raise ValueError(f"Cannot compare pack folder version '{value}'")
    parts = [int(part) for part in value.split(".")]
    return tuple(parts + [0] * (3 - len(parts)))


def minimum_java_version(pack_version: str) -> int:
    parsed_version = parse_pack_version(pack_version)
    for rule_version, java_version in JAVA_MINIMUM_RULES:
        if parsed_version >= parse_pack_version(rule_version):
            return java_version
    return 0


def resolved_java_version(pack_version: str, metadata_java_version: int) -> int:
    return max(metadata_java_version, minimum_java_version(pack_version))


def artifact_url(minecraft_version: str, runtime_test_version: str) -> str:
    artifact = f"mc-runtime-test-{minecraft_version}-{runtime_test_version}-fabric-release.jar"
    return (
        "https://github.com/headlesshq/mc-runtime-test/releases/download/"
        f"{runtime_test_version}/{artifact}"
    )


def artifact_check_mode() -> str:
    return os.getenv("RUNTIME_TEST_ARTIFACT_CHECK", "remote").lower()


def runtime_artifact_exists(minecraft_version: str, runtime_test_version: str) -> bool:
    check_mode = artifact_check_mode()
    if check_mode in {"runtime", "mock-runtime"}:
        return True
    if check_mode in {"boot", "mock-boot", "offline"}:
        return False
    if check_mode == "mock":
        mocked_versions = {
            version.strip()
            for version in os.getenv("RUNTIME_TEST_RUNTIME_ARTIFACTS", "").split(",")
            if version.strip()
        }
        return "*" in mocked_versions or minecraft_version in mocked_versions
    if check_mode != "remote":
        raise ValueError(
            "RUNTIME_TEST_ARTIFACT_CHECK must be one of remote, runtime, boot, "
            "mock-runtime, mock-boot, offline, or mock"
        )

    head_result = head_request_exists(artifact_url(minecraft_version, runtime_test_version))
    if head_result is not None:
        return head_result

    api_result = github_api_asset_exists(minecraft_version, runtime_test_version)
    if api_result is not None:
        return api_result

    print(
        f"Warning: could not verify runtime-test artifact for Minecraft {minecraft_version}; "
        "falling back to boot mode.",
        file=sys.stderr,
    )
    return False


def head_request_exists(url: str) -> bool | None:
    transient_error = False
    for attempt in range(3):
        request = urllib.request.Request(url, method="HEAD")
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                return 200 <= response.status < 400
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return False
            if error.code in {403, 429, 500, 502, 503, 504}:
                transient_error = True
            else:
                raise
        except (TimeoutError, urllib.error.URLError):
            transient_error = True

        if attempt < 2:
            time.sleep(2**attempt)

    if transient_error:
        print("Warning: HEAD artifact check failed transiently.", file=sys.stderr)
    return None


def github_api_asset_exists(
    minecraft_version: str,
    runtime_test_version: str,
) -> bool | None:
    asset_name = f"mc-runtime-test-{minecraft_version}-{runtime_test_version}-fabric-release.jar"
    request = urllib.request.Request(
        "https://api.github.com/repos/headlesshq/mc-runtime-test/releases/tags/"
        f"{runtime_test_version}",
        headers=github_headers(),
    )

    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                payload = json.load(response)
            return any(asset.get("name") == asset_name for asset in payload.get("assets", []))
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return False
            if error.code not in {403, 429, 500, 502, 503, 504}:
                raise
        except (TimeoutError, urllib.error.URLError, json.JSONDecodeError):
            pass

        if attempt < 2:
            time.sleep(2**attempt)

    return None


def resolve_runtime_test_version() -> str:
    requested_version = os.getenv("MC_RUNTIME_TEST_VERSION", "").strip()
    if requested_version and requested_version.lower() != "latest":
        return requested_version

    fallback_version = (
        os.getenv("MC_RUNTIME_TEST_FALLBACK_VERSION", "").strip()
        or DEFAULT_RUNTIME_TEST_FALLBACK_VERSION
    )
    if artifact_check_mode() in MOCK_ARTIFACT_CHECK_MODES:
        return fallback_version

    latest_version = github_latest_release_version()
    if latest_version:
        return latest_version

    print(
        f"Warning: could not resolve latest mc-runtime-test release; "
        f"falling back to {fallback_version}.",
        file=sys.stderr,
    )
    return fallback_version


def github_latest_release_version() -> str | None:
    request = urllib.request.Request(
        "https://api.github.com/repos/headlesshq/mc-runtime-test/releases/latest",
        headers=github_headers(),
    )

    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                payload = json.load(response)
            tag_name = str(payload.get("tag_name", "")).strip()
            return tag_name or None
        except urllib.error.HTTPError as error:
            if error.code not in {403, 429, 500, 502, 503, 504}:
                raise
        except (TimeoutError, urllib.error.URLError, json.JSONDecodeError):
            pass

        if attempt < 2:
            time.sleep(2**attempt)

    return None


def github_headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def matrix_entry(
    pack_dir: Path,
    metadata_module: ModuleType,
    runtime_test_version: str,
) -> dict[str, str]:
    metadata: dict[str, Any] = metadata_module.read_pack_metadata(pack_dir / "pack.toml")
    minecraft_version = str(metadata["minecraft_version"])
    java = resolved_java_version(pack_dir.name, int(metadata["java_version"]))
    mode = (
        "runtime"
        if runtime_artifact_exists(minecraft_version, runtime_test_version)
        else "boot"
    )
    return {
        "version": pack_dir.name,
        "mode": mode,
        "java": str(java),
        "runtime_test_version": runtime_test_version,
    }


def selected_pack_dirs(modrinth_dir: Path, requested_version: str) -> list[Path]:
    if requested_version == "all":
        return discover_pack_dirs(modrinth_dir)

    pack_dir = modrinth_dir / requested_version
    pack_path = pack_dir / "pack.toml"
    if not pack_path.is_file():
        raise SystemExit(
            f"Requested Modrinth pack folder '{requested_version}' was not found at {pack_path}"
        )
    return [pack_dir]


def main() -> None:
    repo_root = Path.cwd()
    requested_version = os.getenv("REQUESTED_VERSION", "all").strip() or "all"
    metadata_module = load_metadata_module()
    pack_dirs = selected_pack_dirs(repo_root / "modrinth", requested_version)
    runtime_test_version = resolve_runtime_test_version()
    matrix = [
        matrix_entry(pack_dir, metadata_module, runtime_test_version)
        for pack_dir in pack_dirs
    ]
    print(json.dumps(matrix, separators=(",", ":")))


if __name__ == "__main__":
    main()
