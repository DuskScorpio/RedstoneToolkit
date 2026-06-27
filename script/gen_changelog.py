#!/usr/bin/env python3
"""
Generate changelog.md content for RedstoneToolkit.

Usage:
    python3 gen_changelog.py [BASE_REF]
    BASE_REF defaults to 'bb754d4' if omitted.

Writes result to stdout.
"""
import subprocess, re, sys, tomllib
from collections import defaultdict
from pathlib import Path

BASE_DEFAULT = "bb754d4"
REPO = Path("/home/duskscorpio/repos/RedstoneToolkit")
VERSIONS = ['1.16.5','1.17.1','1.18.2','1.19.4','1.20.6','1.21.0','1.21.11','26.1.2','26.2.0','26.3.0']

def normalize_version_key(v: str) -> str:
    """Normalize version keys for comparison (e.g., '26.2' matches '26.2.0')."""
    v = v.strip().rstrip(':')
    if v.endswith('.0'):
        candidate = v[:-2]
        if candidate.replace('.', '').isdigit():
            return candidate
    return v

def resolve_base(cli_base: str | None = None) -> str:
    if cli_base:
        return cli_base
    tags = subprocess.run(
        ['git', 'ls-remote', '--tags', 'origin', 'release/*'],
        cwd=REPO, capture_output=True, text=True,
    ).stdout.splitlines()
    tags = [t.split('/')[-1] for t in tags if t]
    tags.sort(key=lambda v: [int(x) for x in re.split(r'[^0-9]', v)[:3] if x])
    if not tags:
        return BASE_DEFAULT
    latest = tags[-1]
    r = subprocess.run(
        ['git', 'rev-list', '-n', '1', f'refs/tags/release/{latest}'],
        cwd=REPO, capture_output=True, text=True,
    )
    return r.stdout.strip() or BASE_DEFAULT


def show(path: str) -> str:
    r = subprocess.run(
        ['git', 'show', f'{base}:{path}'],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    return r.stdout if r.returncode == 0 else ''


base = sys.argv[1] if len(sys.argv) > 1 else resolve_base()


def get_mc_version(folder: str) -> str:
    """Read minecraft version from pack.toml in the given version folder."""
    for platform in ['modrinth', 'curseforge']:
        pack = REPO / platform / folder / 'pack.toml'
        if pack.exists():
            try:
                data = tomllib.loads(pack.read_text())
                return data.get('versions', {}).get('minecraft', folder)
            except Exception:
                pass
    return folder


def find_all_version_folders() -> list[str]:
    """Find all version folders ordered by VERSIONS (modrinth only)."""
    folders = set()
    p = REPO / 'modrinth'
    if p.exists():
        for d in p.iterdir():
            if d.is_dir() and (d / 'pack.toml').exists():
                folders.add(d.name)
    return sorted(folders, key=lambda v: VERSIONS.index(v) if v in VERSIONS else 999)


def load_file_list() -> tuple[list[dict], dict]:
    """Load file_list.yml entries and return (entries, slug_to_name)."""
    f = REPO / 'file_list.yml'
    if not f.exists():
        return [], {}
    try:
        import yaml
        data = yaml.safe_load(f.read_bytes().decode('utf-8-sig').replace('\r\n', '\n').replace('\r', '\n'))
    except Exception:
        return [], {}
    entries = data.get('enabled_files', []) if isinstance(data, dict) else []
    slug_to_name = {}
    for e in entries:
        if not isinstance(e, dict):
            continue
        slug = e.get('mr_slug', '')
        name = e.get('name', '')
        if slug and not name:
            name = slug.replace('-', ' ').replace('_', ' ').title()
        if slug and name:
            slug_to_name[slug] = name
    return entries, slug_to_name


def resolve_mod_name(slug: str, version: str, slug_to_name: dict) -> str:
    """Resolve display name for a mod .pw.toml file."""
    pw = REPO / 'modrinth' / version / 'mods' / f'{slug}.pw.toml'
    if pw.exists():
        try:
            content = pw.read_text()
            m = re.search(r'^name = "(.*)"', content, re.MULTILINE)
            if m:
                return m.group(1)
        except Exception:
            pass
    return slug_to_name.get(slug, slug.replace('-', ' ').replace('_', ' ').title())


def normalize_version_key(v: str) -> str:
    """Normalize version keys for comparison (e.g., '26.2' matches '26.2.0')."""
    v = v.strip()
    if v.endswith('.0'):
        candidate = v[:-2]
        if candidate.replace('.', '').isdigit():
            return candidate
    return v


def get_mods_for_version(version: str, entries: list[dict], slug_to_name: dict) -> list[str]:
    """Get expected mod display names for a version folder from file_list.yml entries."""
    names = []
    norm_v = normalize_version_key(version)
    for e in entries:
        if not isinstance(e, dict):
            continue
        slug = e.get('mr_slug', '')
        if not slug:
            continue
        version_constraint = e.get('version', '')
        urls = e.get('urls', {}) if isinstance(e.get('urls'), dict) else {}
        if urls:
            has_url = any(normalize_version_key(k) == norm_v for k in urls)
        elif version_constraint:
            has_url = (
                norm_v == normalize_version_key(version_constraint)
                or f'{version}/' in version_constraint
                or f'{norm_v}/' in version_constraint
            )
        else:
            has_url = True
        if has_url:
            names.append(slug)
    return sorted(set(names))


all_current_versions = find_all_version_folders()

# Resolve base versions from pack.toml, not folder names
base = resolve_base()
show = lambda path: subprocess.run(['git', 'show', f'{base}:{path}'], cwd=REPO, capture_output=True, text=True).stdout if path else ''
base_versions = {}
for platform in ['modrinth', 'curseforge']:
    p = REPO / platform
    if not p.exists():
        continue
    for d in p.iterdir():
        if not d.is_dir():
            continue
        rel = f"{platform}/{d.name}/pack.toml"
        content = show(rel)
        if content:
            try:
                data = tomllib.loads(content)
                mv = data.get('versions', {}).get('minecraft', d.name)
                base_versions[d.name] = mv
            except Exception:
                pass

fl_entries, fl_slug_to_name = load_file_list()
news_lines_added = []
news_lines_compat = []

# Compare current mc versions against base mc versions
current_mc_versions = {}
for v in all_current_versions:
    current_mc_versions[v] = get_mc_version(v)

for folder, mc in sorted(current_mc_versions.items(), key=lambda x: VERSIONS.index(x[0]) if x[0] in VERSIONS else 999):
    base_mc = base_versions.get(folder)
    is_new_folder = base_mc is None
    has_new_mc = base_mc is not None and mc != base_mc
    if is_new_folder or has_new_mc:
        news_lines_added.append(f"- Added {mc}")

new_folders = {
    folder for folder, mc in current_mc_versions.items()
    if f"- Added {mc}" in news_lines_added
}

for v in all_current_versions:
    slugs = get_mods_for_version(v, fl_entries, fl_slug_to_name)
    if not slugs:
        continue
    # Skip versions already listed in ## News (newly added or MC-changed)
    if v in new_folders:
        continue
    # resolve display names from .pw.toml files where possible
    names = []
    seen = set()
    for slug in slugs:
        if slug in seen:
            continue
        seen.add(slug)
        pw = REPO / 'modrinth' / v / 'mods' / f'{slug}.pw.toml'
        if pw.exists():
            try:
                content = pw.read_text()
                m = re.search(r'^name = "(.*)"', content, re.MULTILINE)
                if m:
                    names.append(m.group(1))
                    continue
            except Exception:
                pass
        names.append(fl_slug_to_name.get(slug, slug.replace('-', ' ').replace('_', ' ').title()))
    if names:
        news_lines_compat.append((get_mc_version(v), names))

all_changed = subprocess.run(
    ['git', 'diff', base, '--name-only'],
    cwd=REPO,
    capture_output=True,
    text=True,
).stdout.splitlines()

changed = [
    l.strip()
    for l in all_changed
    if l.strip() and re.match(r'^modrinth/[^/]+/mods/[^/]+\.pw\.toml$', l.strip())
]

new_files = []
existing_changed = []
for f in changed:
    if show(f) == '':
        new_files.append(f)
    else:
        existing_changed.append(f)

slug_to_name = {}
for f in set(changed):
    content = show(f)
    m = re.search(r'^name = "(.*)"', content, re.MULTILINE)
    if m:
        slug_to_name[f.split('/')[-1].replace('.pw.toml', '')] = m.group(1)

# Also read current working tree names for newly-added files with no base version
for f in new_files:
    try:
        content = (REPO / f).read_text()
        m = re.search(r'^name = "(.*)"', content, re.MULTILINE)
        if m:
            slug_to_name[f.split('/')[-1].replace('.pw.toml', '')] = m.group(1)
    except Exception:
        pass

# Newly compatible mods: mods that exist in current working tree but NOT in the base for any version
current_mod_files = set()
for platform in ['modrinth', 'curseforge']:
    p = REPO / platform
    if p.exists():
        for d in p.iterdir():
            if d.is_dir():
                mods_dir = d / 'mods'
                if mods_dir.exists():
                    for f in mods_dir.glob('*.pw.toml'):
                        current_mod_files.add(f'{d.name}/{f.name}')

newly_compat = defaultdict(list)
for f in current_mod_files:
    folder = f.split('/')[0]
    if folder == '26.3.0':
        continue
    # Check if this mod+version combo existed at base
    base_path = f'modrinth/{f}'
    if show(base_path) == '' and (REPO / 'modrinth' / f).exists():
        slug = f.split('/')[-1].replace('.pw.toml', '')
        name = slug_to_name.get(slug)
        if name is None:
            try:
                content = (REPO / 'modrinth' / f).read_text()
                m = re.search(r'^name = "(.*)"', content, re.MULTILINE)
                if m:
                    name = m.group(1)
            except Exception:
                pass
        if name:
            newly_compat[folder].append(name)

mod_versions = defaultdict(set)
for f in existing_changed:
    p = f.split('/')
    mod_versions[p[3].replace('.pw.toml', '')].add(p[1])

for f in new_files:
    p = f.split('/')
    mod_versions[p[3].replace('.pw.toml', '')].add(p[1])

latest_folder = all_current_versions[-1] if all_current_versions else '26.3.0'
all_current_mc_versions = {v: get_mc_version(v) for v in all_current_versions}

updates = defaultdict(list)
for mod, vers in mod_versions.items():
    # Drop mods only in newly-added versions, AND any version listed in ## News
    skip_vers = {latest_folder} | new_folders
    filtered = [v for v in vers if v not in skip_vers]
    if not filtered:
        continue
    present = sorted(filtered, key=VERSIONS.index)
    if not present:
        continue
    # Use mc version strings in the key when available, fall back to folder name
    start_mc = all_current_mc_versions.get(present[0], present[0])
    end_mc = all_current_mc_versions.get(present[-1], present[-1])
    key = f"{start_mc}-{end_mc}:" if start_mc != end_mc else f"{start_mc}:"
    updates[key].append(mod)

out = ["## News", ""]
out.extend(news_lines_added)

# Resolve display names for newly_compat from .pw.toml files
if any(newly_compat.values()):
    out.append("- Added newly compatible mods to:")
    for v in sorted(newly_compat, key=lambda x: VERSIONS.index(x) if x in VERSIONS else 999):
        out.append(f"  - {get_mc_version(v)}:")
        for slug in sorted(set(newly_compat[v])):
            name = resolve_mod_name(slug, v, slug_to_name)
            out.append(f"    - {name}")

out += ["", "## Changes", "", "## Updates", ""]
def updates_sort_key(k: str):
    parts = k.rstrip(':').split('-')
    start = parts[0]
    end = parts[-1]
    def idx(v: str):
        base = normalize_version_key(v)
        if base not in VERSIONS:
            candidate = base + '.0'
            if candidate in VERSIONS:
                base = candidate
        return VERSIONS.index(base) if base in VERSIONS else 999
    s = idx(start)
    e = idx(end)
    span = e - s + 1
    return (-span, s, e)

for key in sorted(updates, key=updates_sort_key):
    out.append(f"- {key}")
    for m in sorted(updates[key]):
        out.append(f"  - {resolve_mod_name(m, latest_folder, slug_to_name)}")

print('\n'.join(out))
