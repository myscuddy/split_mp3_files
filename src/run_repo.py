import os
import json
import platform
from datetime import datetime
from pathlib import Path


# Module-level variable to store the runs directory
_runs_dir = None


def _get_default_runs_dir():
    """Determine the default runs directory with fallback logic.
    
    Priority:
    1. $HOME/.config/split_mp3_files (Linux/macOS)
    2. %AppData%/Roaming/split_mp3_files (Windows)
    3. /tmp/split_mp3_files (Linux/macOS, if #1 fails)
    4. Temp directory with split_mp3_files (Windows, if #2 fails)
    
    Returns:
        str: The path to the runs directory
    """
    is_windows = platform.system() == "Windows"
    
    if is_windows:
        # Windows: Use AppData/Roaming
        try:
            appdata = os.environ.get("APPDATA")
            if appdata:
                runs_dir = os.path.join(appdata, "split_mp3_files")
            else:
                runs_dir = str(Path.home() / "AppData" / "Roaming" / "split_mp3_files")
            
            # Try to create and verify write access
            os.makedirs(runs_dir, exist_ok=True)
            test_file = os.path.join(runs_dir, ".write_test")
            with open(test_file, "w") as f:
                f.write("")
            os.remove(test_file)
            return runs_dir
        except Exception:
            # Fallback to temp directory
            import tempfile
            return os.path.join(tempfile.gettempdir(), "split_mp3_files")
    else:
        # Linux/macOS: Try ~/.config first
        try:
            home = os.path.expanduser("~")
            runs_dir = os.path.join(home, ".config", "split_mp3_files")
            
            # Try to create and verify write access
            os.makedirs(runs_dir, exist_ok=True)
            test_file = os.path.join(runs_dir, ".write_test")
            with open(test_file, "w") as f:
                f.write("")
            os.remove(test_file)
            return runs_dir
        except Exception:
            # Fallback to /tmp
            return "/tmp/split_mp3_files"


def set_runs_dir(runs_dir):
    """Set the runs directory to use for all operations.
    
    Args:
        runs_dir: Path to the directory where runs.json should be stored.
                 If None, uses the default directory.
    """
    global _runs_dir
    _runs_dir = runs_dir


def _default_repo_dir():
    """Return the configured or default runs directory.
    
    Returns:
        str: Path to the runs directory
    """
    if _runs_dir is not None:
        return _runs_dir
    return _get_default_runs_dir()


def _ensure_migration():
    """Run migration on first use to convert old format to new single-file format."""
    try:
        from migrate_runs import migrate_to_single_file
        migrate_to_single_file()
    except Exception:
        pass


_ensure_migration()


def _runs_file_path(repo_dir=None) -> str:
    """Return the path to the single runs.json file."""
    repo_dir = repo_dir or _default_repo_dir()
    os.makedirs(repo_dir, exist_ok=True)
    return os.path.join(repo_dir, "runs.json")


def _load_all_runs(repo_dir=None) -> list:
    """Load all runs from the single runs.json file."""
    fpath = _runs_file_path(repo_dir)
    if not os.path.isfile(fpath):
        return []
    try:
        with open(fpath, "r", encoding="utf-8") as fh:
            data = json.load(fh)
            # ensure list
            if isinstance(data, list):
                return data
    except Exception:
        pass
    return []


def _save_all_runs(all_runs: list, repo_dir=None):
    """Save all runs to the single runs.json file."""
    fpath = _runs_file_path(repo_dir)
    try:
        with open(fpath, "w", encoding="utf-8") as fh:
            json.dump(all_runs, fh, indent=2, ensure_ascii=False)
    except Exception:
        pass


def load_runs(path: str, repo_dir=None):
    """Load all runs for a specific source file.
    
    Args:
        path: The source MP3 file path
        repo_dir: Optional repository directory (defaults to run_repo/)
    
    Returns:
        List of run entries for the specified source file, newest first
    """
    all_runs = _load_all_runs(repo_dir)
    # Filter runs for the specific source file
    filtered = [r for r in all_runs if r.get("source_file") == path]
    return filtered


def save_run(path: str, options: dict, repo_dir=None, max_versions=10):
    """Save a run for the given source path. Keeps up to max_versions distinct runs per source.

    Distinctness is determined by equality of the `options` dict.
    Newer runs are placed first.
    
    Args:
        path: The source MP3 file path
        options: The options/settings dict to save
        repo_dir: Optional repository directory (defaults to run_repo/)
        max_versions: Maximum number of runs to keep per source file
    """
    all_runs = _load_all_runs(repo_dir)
    
    # Normalize options by removing transient fields if any
    normalized = dict(options)
    
    # Remove existing runs for this source file and keep track of other sources' runs
    other_runs = [r for r in all_runs if r.get("source_file") != path]
    source_runs = [r for r in all_runs if r.get("source_file") == path]
    
    # Remove existing identical entries from this source's runs
    source_runs = [r for r in source_runs if r.get("options") != normalized]
    
    # Create new entry with source_file as first field
    entry = {
        "source_file": path,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "options": normalized,
    }
    
    source_runs.insert(0, entry)
    # truncate to max_versions
    source_runs = source_runs[:max_versions]
    
    # Combine all runs (other sources + updated source runs)
    new_all_runs = other_runs + source_runs
    
    _save_all_runs(new_all_runs, repo_dir)


def get_repo_file_for_path(path: str, repo_dir=None) -> str:
    """Return the repository JSON file path.
    
    Note: Since we now use a single runs.json file, this returns the path to that file
    regardless of the source file path (for backward compatibility).
    """
    return _runs_file_path(repo_dir)

