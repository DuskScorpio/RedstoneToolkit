## Setting up (VS Code)

1. Run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` in PowerShell as Admin
2. `Ctrl+Shift+P` > `Python: Create Environment` > `venv` in VS Code to setup virtual environment
3. Run `pip install -r requirements.txt` to install prerequisites

## CLI

Use `python -m script --help` in a virtual environment for more information!

### Helper

Start it with `python -m script helper`, It provides you with many parameter hints and autocompletion

You don't need to type the `python -m script` prefix, it's already included

## Testing modpack

1. Follow instructions from [this video](https://www.bilibili.com/video/BV1YQhyz5EHf) or [this guide](https://docs.yw-games.top/posts/tutorial/modpack/packwiz.html)
2. Run `../tools/packwiz serve` within a game version folder, e.g. `modrinth/1.21.11`

### Runtime test workflow

The GitHub Actions runtime test lives in `.github/workflows/runtime-test.yml`.
It uses `packwiz serve`, `packwiz-installer`, and `headlesshq/mc-runtime-test`
to launch the selected Modrinth pack in a headless Minecraft client.

The workflow only tests the Modrinth pack folders. It does not run the
CurseForge export or CurseForge pack folders.

The workflow needs these files in the repository:

- `tools/packwiz`
- `tools/packwiz-installer-bootstrap.jar`
- `tools/packwiz-installer.jar`
- `internal-files/`
- `modrinth/<version>/pack.toml`

`packwiz-installer` may print `Resolving CurseForge metadata` while it installs
the pack. That is normal packwiz-installer behavior. The workflow still tests
only the Modrinth pack folders and does not build or launch CurseForge exports.

GitHub Actions runs all listed versions by default. Pushes to `main`, matching
pull requests, and manual runs with `version=all` use the full matrix. Manual
runs can test one folder by choosing a specific `version` value.

By default, the workflow chooses Java from the Minecraft version. Some older
pack folders intentionally contain newer mods, so their workflow matrix entries
override Java explicitly:

- `1.16.5` uses Java 17
- `1.17.1` uses Java 17
- `1.19.4` uses Java 21

Full runtime tests use the `mc-runtime-test` mod to launch Minecraft, create a
test world, run any available game tests, and close the client. These versions
currently run full runtime tests:

- `1.16.5`
- `1.17.1`
- `1.18.2`
- `1.19.4`
- `1.20.6`
- `1.21.0`
- `1.21.11`
- `26.1.2`

Newer versions that do not have a matching `mc-runtime-test` jar run a basic
HeadlessMC boot test instead. The boot test installs the pack, launches the
Fabric client under Xvfb, waits for Minecraft's renderer boot marker, then
closes the client:

- `26.2.0`
- `26.3.0`

Known pack issues:

- `1.19.4` starts with Java 21, but currently fails on an
  `carpet-igny-addition` mixin descriptor error.
- `1.21.0` currently fails dependency resolution because some selected mods
  target newer `1.21.x` versions.

For GitHub Actions, no local setup is required. Push the workflow and run
`runtime-test` from the Actions tab, or let it run on matching pull requests
and pushes.

To watch progress on GitHub, open the repository's Actions tab, choose the
`runtime-test` run, then open the running `runtime-test` job and expand the
version you care about. Logs stream live while the job runs. When a GitHub run
finishes, the workflow uploads `runtime-test-logs-modrinth-...` artifacts with
the packwiz server log, Minecraft logs, and crash reports.

For local testing with `act`, install:

- Docker
- `act`

On Windows, Docker Desktop also requires WSL2:

```powershell
winget install --id Docker.DockerDesktop --exact
wsl --install
```

After rebooting if prompted, launch Docker Desktop and confirm Docker works:

```powershell
docker info
```

On Linux, install Docker with your distribution's package manager, then install
`act` from <https://github.com/nektos/act/releases> or your package manager.
Make sure your user can run Docker, or prefix the `act` command with `sudo`.

Run the default Modrinth pack runtime test locally:

```powershell
.\.cache\act\act.exe workflow_dispatch `
  -W .github\workflows\runtime-test.yml `
  --input version=1.21.11 `
  -P ubuntu-latest=catthehacker/ubuntu:act-latest
```

On Linux, use the same arguments with the `act` binary:

```bash
act workflow_dispatch \
  -W .github/workflows/runtime-test.yml \
  --input version=1.21.11 \
  -P ubuntu-latest=catthehacker/ubuntu:act-latest
```

To run the full matrix locally, use `--input version=all`. This can take a
while because it installs and launches every listed pack version. Local `act`
runs print progress directly in the terminal, including each workflow step and
the Minecraft launch output.

## `file_list.yml` Example

```yaml
enabled_files:
  - mr_slug: lithium # Optional
    cf_slug: lithium # Optional
    version: ">=1.16.4" # Optional
    # Optional
    # name and urls must exist at the same time or not at the same time
    name: lithium
    urls:
      1.21.1: "https://github.com/CaffeineMC/lithium/releases/download/mc1.21.1-0.15.1/lithium-fabric-0.15.1+mc1.21.1.jar"
      1.21.11: "https://github.com/CaffeineMC/lithium/releases/download/mc1.21.11-0.21.2/lithium-fabric-0.21.2+mc1.21.11.jar"
disabled_files:
  - mr_slug: iris
```
