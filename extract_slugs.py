import os
import re

# Path configuration
index_dir = "."  # Run this inside the .index folder
output_file = "../master_mods.txt"

slug_pattern = re.compile(r'slug\s*=\s*"(.*)"')
slugs = set()

if os.path.exists(index_dir):
    for filename in os.listdir(index_dir):
        if filename.endswith(".pw.toml"):
            with open(os.path.join(index_dir, filename), 'r', encoding='utf-8') as f:
                content = f.read()
                match = slug_pattern.search(content)
                if match:
                    slugs.add(match.group(1))

    with open(output_file, 'w', encoding='utf-8') as f:
        for slug in sorted(slugs):
            f.write(f"{slug}\n")
    
    print(f"Done! Saved {len(slugs)} slugs to {output_file}")
else:
    print("Error: Could not find the .index directory.")