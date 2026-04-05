from enum import StrEnum, auto
from pathlib import Path
from github import Github, Auth

import re
import os
import json
import tomllib

class PlatForm(StrEnum):
    MODRINTH = auto()
    CURSEFORGE = auto()

class DataType(StrEnum):
    MC_VERS = auto()
    DIR_MAP = auto()
    TYPE_MAP = auto()
    VER_MAP = auto()
    PUBLISH = auto()

class __CACHE(StrEnum):
    TAGS = auto()
    ASSETS = auto()

CACHE = {
    __CACHE.TAGS: list(),
    __CACHE.ASSETS: dict(),
    'flag': False
}

def main():
    create_tag_list = [i for i in get_vers() if not tag_exists(f'release/{i}')]
    json_data = {
        'create': create_tag_list,
        'should_create': len(create_tag_list) != 0,
        PlatForm.MODRINTH: get_data(PlatForm.MODRINTH),
        PlatForm.CURSEFORGE: get_data(PlatForm.CURSEFORGE)
    }
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(json_data, f)


def get_data(platform: PlatForm) -> dict[str, list[str] | dict[str, str]]:
    dirs = [i.name for i in Path(platform).iterdir() if i.joinpath('pack.toml').exists()]
    data = {
        DataType.MC_VERS: list(),
        DataType.DIR_MAP: dict(),
        DataType.TYPE_MAP: dict(),
        DataType.VER_MAP: dict(),
        DataType.PUBLISH: False
    }
    for mc_dir in dirs:
        path = Path(platform).joinpath(mc_dir).joinpath('pack.toml')
        with open(path, 'rb') as f:
            toml = tomllib.load(f)
        mc_ver = toml['versions']['minecraft']
        pack_ver = toml['version']
        if file_exists(platform, mc_ver, pack_ver): continue
        data[DataType.MC_VERS].append(mc_ver)
        data[DataType.DIR_MAP][mc_ver] = mc_dir
        if re.match('.*alpha\\.\\d+', pack_ver): raise ValueError
        pack_type = 'beta' if re.match('.*(beta|rc)\\.\\d+', pack_ver) else 'release'
        data[DataType.TYPE_MAP][mc_ver] = pack_type
        data[DataType.VER_MAP][mc_ver] = pack_ver
    if len(data[DataType.MC_VERS]) != 0:
        data[DataType.PUBLISH] = True
    return data


def file_exists(platform: PlatForm, mc_ver: str, pack_ver: str) -> bool:
    suffix = {
        PlatForm.MODRINTH: '.mrpack',
        PlatForm.CURSEFORGE: '.zip'
    }[platform]
    name = re.sub('.*/', '', os.getenv('GITHUB_REPOSITORY', 'DuskScorpio/RedstoneToolkit'))
    file_name = f'{name}-{pack_ver}+mc{mc_ver}{suffix}'
    tag = f'release/{pack_ver}'
    if not tag_exists(tag):
        return False
    if pack_ver in CACHE[__CACHE.ASSETS]:
        return file_name in CACHE[__CACHE.ASSETS][pack_ver]
    with Github(auth=get_auth()) as g:
        repo = g.get_repo(os.getenv('GITHUB_REPOSITORY', 'DuskScorpio/RedstoneToolkit'))
        assets = [i.name for i in repo.get_release(tag).get_assets()]
        CACHE[__CACHE.ASSETS][pack_ver] = assets
        return file_name in assets


def get_vers() -> list[str]:
    vers = list()
    for platform in PlatForm:
        pack_paths = [i.joinpath('pack.toml') for i in Path(platform).iterdir() if i.joinpath('pack.toml').exists()]
        for pack_path in pack_paths:
            with open(pack_path, 'rb') as f:
                vers.append(tomllib.load(f)['version'])
    return list(set(vers))


def tag_exists(tag: str) -> bool:
    if CACHE[__CACHE.TAGS] or CACHE['flag']:
        return tag in CACHE[__CACHE.TAGS]
    else:
        with Github(auth=get_auth()) as g:
            repo = g.get_repo(os.getenv('GITHUB_REPOSITORY', 'DuskScorpio/RedstoneToolkit'))
            tags = [i.tag_name for i in repo.get_releases()]
            CACHE[__CACHE.TAGS].extend(tags)
            CACHE['flag'] = True
            return tag in tags


def get_auth():
    token = os.getenv('GH_TOKEN')
    if token is None:
        return None
    else:
        return Auth.Token(token)

if __name__ == '__main__':
    main()
    del CACHE