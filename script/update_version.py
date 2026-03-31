#!/usr/bin/env python3
"""
Update version in all pack.toml files across modrinth and curseforge directories.
Usage: python update_version.py <new_version>
Example: python update_version.py 0.5.0
"""

import sys
import re
from pathlib import Path

def update_pack_version(new_version):
    """Update version in all pack.toml files."""
    workspace_root = Path(__file__).parent.parent
    
    # Find all pack.toml files
    pack_files = list(workspace_root.glob("modrinth/*/pack.toml")) + \
                 list(workspace_root.glob("curseforge/*/pack.toml"))
    
    if not pack_files:
        print("No pack.toml files found!")
        return False
    
    updated_count = 0
    for pack_file in sorted(pack_files):
        try:
            content = pack_file.read_text(encoding='utf-8')
            
            # Replace version line
            new_content = re.sub(
                r'version = "[^"]*"',
                f'version = "{new_version}"',
                content
            )
            
            if new_content != content:
                pack_file.write_text(new_content, encoding='utf-8')
                print(f"✓ Updated {pack_file.relative_to(workspace_root)}")
                updated_count += 1
            else:
                print(f"- No changes needed for {pack_file.relative_to(workspace_root)}")
        except Exception as e:
            print(f"✗ Error updating {pack_file}: {e}")
    
    print(f"\nTotal updated: {updated_count}/{len(pack_files)}")
    return updated_count > 0

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python update_version.py <new_version>")
        print("Example: python update_version.py 0.5.0")
        sys.exit(1)
    
    new_version = sys.argv[1]
    
    # Validate version format
    if not re.match(r'^\d+\.\d+\.\d+$', new_version):
        print(f"Error: Invalid version format '{new_version}'. Expected format: X.Y.Z")
        sys.exit(1)
    
    print(f"Updating all pack.toml files to version {new_version}...\n")
    success = update_pack_version(new_version)
    sys.exit(0 if success else 1)
