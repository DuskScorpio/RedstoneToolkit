import os
import subprocess

# --- Configuration ---
master_file = "master_mods.txt"

def get_version_folders():
    """Finds all subdirectories that contain a packwiz pack.toml file."""
    folders = []
    for d in os.listdir('.'):
        if os.path.isdir(d) and not d.startswith('.') and d != 'git':
            # We check if it's a packwiz folder by looking for pack.toml
            if os.path.exists(os.path.join(d, "pack.toml")):
                folders.append(d)
    return folders

def sync():
    if not os.path.exists(master_file):
        print(f"Error: {master_file} not found!")
        return

    # 1. Read the Master List 
    with open(master_file, 'r', encoding='utf-8') as f:
        # Filter for lines that start with an ID (ignore comments)
        lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    # 2. Detect Version Folders 
    version_folders = get_version_folders()
    
    if not version_folders:
        print("No version folders with pack.toml found! Create a folder (e.g., 1.21.11) and run 'packwiz init' inside it first.")
        return

    print(f"Detected versions: {', '.join(version_folders)}")

    for v in version_folders:
        print(f"\n>>> Syncing Pack Folder: {v} <<<")
        os.chdir(v)

        for line in lines:
            # Parse: [ID] # [Name] !skip:[version]
            parts = line.split('#')
            mod_id = parts[0].strip()
            
            # 3. Handle Skipping Logic from Master List 
            if "!skip:" in line:
                # Extract the version string after the tag
                skip_content = line.split("!skip:")[1].split()[0]
                # Split by comma in case of multiple versions like !skip:1.20.1,1.21
                skipped_versions = [s.strip() for s in skip_content.split(",")]
                
                if v in skipped_versions:
                    print(f"  [SKIPPED] {mod_id} (excluded for {v})")
                    continue

            print(f"  Adding: {mod_id}")
            # Use --y to auto-confirm and --required for standard setup
            subprocess.run(["packwiz", "mr", "add", mod_id, "--required", "--y"], capture_output=True)

        # 4. Refresh to catch manual JARs like JoaCarpet or Custom CUI [cite: 2]
        print(f"  Refreshing index for {v}...")
        subprocess.run(["packwiz", "refresh"], capture_output=True)
        
        os.chdir("..")

    print("\n[DONE] All detected versions are synced.")

if __name__ == "__main__":
    sync()