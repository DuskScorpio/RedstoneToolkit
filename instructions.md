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
