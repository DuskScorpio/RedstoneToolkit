## Setting up (VS Code)

1. Run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` in PowerShell as Admin
2. `Ctrl+Shift+P` > `Python: Create Environment` > `venv` in VS Code to setup virtual environment
3. Run `pip install -r script/requirements.txt` to install prerequisites

## Importing mod index

1. Place `.index` folder in the project root `RedstoneTools/`
2. Run `py import_index.py` from `script/`
3. `mod_list.yml` will be generated in `RedstoneTools/`

## Installing mods

1. Create folders for each game version in project root
2. Run `../tools/packwiz init` within each version folder
3. Run `py install.py` from `script/`
4. Use `py install.py -v x.xx.x` will only install for specified version
5. Removing mods from `mod_list.yml` will remove the mods from the version folders when `install.py` runs

## Exporting modpack

1. Run `py export.py` from `script/`
2. Use `py export.py -v x.xx.x` will only export for specified version

## Testing modpack

1. Follow instructions from [this video](https://www.bilibili.com/video/BV1YQhyz5EHf) or [this guide](https://docs.yw-games.top/posts/tutorial/modpack/packwiz.html)
2. Run `../tools/packwiz server` within game version folder, e.g. `RedstoneTools/1.21.11`

## `mod_list.yml` Example

```yaml
enabled_mods:
  - mr_slug: lithium # Optional
    cf_slug: lithium # Optional
    version: ">=1.16.4" # Optional
    # Optional
    # name and urls must exist at the same time or not at the same time
    name: lithium
    urls:
      1.21.1: "https://github.com/CaffeineMC/lithium/releases/download/mc1.21.1-0.15.1/lithium-fabric-0.15.1+mc1.21.1.jar"
      1.21.11: "https://github.com/CaffeineMC/lithium/releases/download/mc1.21.11-0.21.2/lithium-fabric-0.21.2+mc1.21.11.jar"
disabled_mods:
  - mr_slug: iris
```
