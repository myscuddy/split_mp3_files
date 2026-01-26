"""
Migration script to convert old hash-based run_repo files to the new single runs.json format.

The old format stored one JSON file per source file (named by SHA256 hash of the path).
The new format stores all runs in a single runs.json file with source_file as a field.

Since the old files don't contain the source path, we cannot directly migrate them.
This script cleans up old files and initializes an empty runs.json.
"""

import os
import json
import hashlib


def _default_repo_dir():
    here = os.path.dirname(__file__)
    root = os.path.dirname(here)
    return os.path.join(root, "run_repo")


def migrate_to_single_file(repo_dir=None):
    """
    Migrate from old hash-based JSON files to the new single runs.json file.
    
    Since source file paths are not stored in the old format, we cannot fully migrate.
    This function will:
    1. Check if runs.json already exists
    2. If not, create an empty runs.json
    3. Optionally back up old files
    """
    repo_dir = repo_dir or _default_repo_dir()
    os.makedirs(repo_dir, exist_ok=True)
    
    runs_file = os.path.join(repo_dir, "runs.json")
    
    # If new format already exists, nothing to do
    if os.path.isfile(runs_file):
        return
    
    # Create empty runs.json
    try:
        with open(runs_file, "w", encoding="utf-8") as fh:
            json.dump([], fh, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Warning: Could not create {runs_file}: {e}")
    
    # Backup old files by renaming them
    try:
        backup_dir = os.path.join(repo_dir, "old_hash_based")
        old_files = [f for f in os.listdir(repo_dir) if f.endswith(".json") and f != "runs.json"]
        
        if old_files:
            os.makedirs(backup_dir, exist_ok=True)
            for f in old_files:
                old_path = os.path.join(repo_dir, f)
                new_path = os.path.join(backup_dir, f)
                try:
                    os.rename(old_path, new_path)
                except Exception:
                    pass
    except Exception as e:
        print(f"Warning: Could not back up old files: {e}")


if __name__ == "__main__":
    migrate_to_single_file()
    print("Migration complete. Empty runs.json created.")
