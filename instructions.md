## Setting up (VS Code)

1. Run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` in PowerShell as Admin
2. `Ctrl+Shift+P` > `Python: Create Environment` > `venv` in VS Code to setup virtual environment
3. Run `pip install -r requirements.txt` to install prerequisites

## CLI

Use `python -m script --help` in a virtual environment for more information!

### Helper

Start it with `python -m script helper`. It provides parameter hints and autocompletion.

## GitHub Actions

### weekly-sync

Updates all mods, regenerates `changelog.md`, commits, and pushes. Triggers `runtime-test` afterward.

Trigger: `workflow_dispatch` or schedule (`0 9 * * 0` — Sundays at 09:00 UTC).

Manual dispatch parameters:

- `match` (string) — NPM-compliant version filter. Supports exact (`26.3.0`), ranges (`>=1.21.1`, `^1.21.0`), and wildcards (`1.21.x`). Default: `*` (all).

### runtime-test

Tests Modrinth packs in a headless Minecraft client. Uses `packwiz serve`, `packwiz-installer`, and `headlesshq/mc-runtime-test`.

Trigger: `push to main`, `workflow_dispatch`.

- All versions in `modrinth/` are tested by default.
- Versions with a matching `mc-runtime-test` jar run full tests (world creation + game tests).
- Versions without a jar run a HeadlessMC boot test instead.
- Check `runtime-test-matrix.py` for the current matrix.
- Logs and crash reports are uploaded as artifacts.

Manual dispatch parameters:

- `version` (string) — Modrinth pack folder to test, e.g. `26.3.0`. Default: `all`.
- `enable_disabled_mods` (boolean) — Enable all disabled mods before testing. Default: `false`.
