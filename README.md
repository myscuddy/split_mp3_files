# split_mp3_files

Tool to split large MP3 files based on either "Silence detection" (split at gaps of low volume) or fixed time intervals. Features a Tkinter GUI and command-line interface with persistent configuration storage.

## Features

- **Silence Detection Mode**: Automatically detect and split on silence intervals
- **Time-based Splitting**: Split files into fixed-length chunks
- **Adaptive Threshold**: Per-file threshold calculation based on audio loudness
- **GUI and CLI**: Both graphical and command-line interfaces
- **Configuration History**: Automatically stores and loads previous run settings
- **Customizable Output**: Control bitrate (64, 128, 192, 256, 320 kbps), VBR quality, and silence padding
- **Cross-platform**: Runs on Linux, macOS, and Windows

## Requirements
- Python 3.8+ (recommended)
- System `ffmpeg` binary installed and available on `PATH` (pydub relies on it).
- Python deps in `requirements.txt` (install with pip).

Example to install dependencies (create and activate a virtualenv first):

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Configuration Storage

Run configurations are automatically stored in:
- **Linux/macOS**: `~/.config/split_mp3_files/runs.json`
- **Windows**: `%APPDATA%\split_mp3_files\runs.json`
- **Fallback**: `/tmp/split_mp3_files/runs.json` (Linux/macOS) or system temp directory (Windows)

# split_mp3_files

A small utility to split large MP3 files using either silence-detection (split at quiet gaps) or fixed time intervals. Provides both a Tkinter GUI and a CLI with persistent run-history storage.

Highlights:

- Silence detection and time-based splitting
- Adaptive per-file thresholds and analysis helpers
- GUI with recent-runs history and CLI parity
- Cross-platform defaults for run-history storage

**Recommended Python:** 3.10+ (works on 3.8+, but newer interpreters are recommended). System `ffmpeg` is required and must be available on `PATH`.

## Quick setup

Install Python deps from the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Alternatively the helper script `src/setup_env.sh` can install common dependencies (note: it does not install system `ffmpeg` nor system `tk` packages).

## Entry points

- CLI + full GUI: `src/split_mp3_files.py` — this is the main script. Run with `--gui` to start the GUI, or pass CLI flags to run headless.
- Lightweight GUI: `src/main.py` — a simpler GUI wrapper that is also useful for quick local launches.

Example (GUI):

```bash
python src/split_mp3_files.py --gui
```

Example (CLI split on silence):

```bash
python src/split_mp3_files.py \
  --mode Silence \
  --input_files /path/to/episode.mp3 \
  --output_dir ./out_chunks
```

## Common CLI options

- `--mode` : `Silence` or `Time`.
- `--input_files` : One or more MP3 paths.
- `--output_dir` : Destination directory for chunks.
- `--runs_dir` : Override where run history is stored (defaults shown below).
- `--gui` : Start the graphical UI.
- `--min_silence` : Minimum silence length (ms). Default: `1000`.
- `--silence_thresh` : Silence threshold in dBFS. Default: `-40`.
- `--adaptive` : Use per-file adaptive threshold (uses file dBFS + `--silence_offset`).
- `--silence_offset` : dB offset applied when `--adaptive` is used. Default: `-16`.
- `--use_silence_intervals` : In `Time` mode, analyze and split by detected silence intervals.
- `--chunk_length` : Chunk length in ms for `Time` mode. Default: `60000`.
- `--bitrate` / `--vbr_quality` : Output bitrate or VBR quality.
- `--silence_padding` : Padding (ms) added to chunk boundaries. Default: `3000`.
- `--analyze` / `--apply_analysis` : Analyze files for suggested parameters (and optionally apply them).

See the CLI help for full details:

```bash
python src/split_mp3_files.py --help
```

## Run-history / configuration storage

By default the project stores run history in a single `runs.json` file. The code selects an appropriate default location depending on platform and write permissions:

- Linux/macOS (preferred): `~/.config/split_mp3_files/runs.json`
- Windows (preferred): `%APPDATA%\\split_mp3_files\\runs.json`
- Fallback on Linux/macOS: `/tmp/split_mp3_files/runs.json`

You can override this with `--runs_dir /path/to/dir`.

Migration note: older releases used one JSON file per source (hash-based) inside a `run_repo` folder. The repository now migrates on first run and will create a single `runs.json`. Old per-file JSONs (if present) are moved to `run_repo/old_hash_based/` as a backup.

## Helpful files in the repo

- `src/setup_env.sh` — convenience script to create a venv and install common Python packages.
- `src/migrate_runs.py` — migration helper that initializes `runs.json` and moves old hash-based JSON files into `run_repo/old_hash_based/`.
- `requirements.txt` — Python package dependencies.

## Tuning tips

- If splits are missing or too frequent: increase/decrease `--min_silence` and/or adjust `--silence_thresh`.
- Use `--analyze` to produce suggested thresholds and likely split points for a given file.
- Normalizing or converting to mono can improve detection reliability for noisy or uneven recordings.

## Version History

### v1.1.1 (2026-03-01)
- Clarified setup instructions and entry points in README
- Documented migration behavior: old per-file JSONs are backed up to `run_repo/old_hash_based/` and an empty `runs.json` is created on first-run when needed

### v1.1.0 (2026-01-25)
- Single configuration file (`runs.json`) for all sources instead of per-file hashes
- Configurable runs directory via `--runs_dir` parameter with smart defaults
- GUI history list with "Apply Selected Run" and "Run Selected Run" buttons
- Analysis feature to suggest optimal split parameters
- Button layout improvements (Analyze and Start Splitting on same line)
- Better bitrate defaults (256 kbps) with full range support (64-320)
- Cross-platform configuration storage support (Linux/macOS/Windows)
- Improved error handling for config directory creation

### v1.0.0 (Initial Release)
- Silence detection splitting mode
- Time-based splitting mode
- CLI and GUI interfaces
- Basic configuration storage

## Contributing

- Add unit/integration tests and small sample audio files to reproduce edge cases.
- Improve preprocessing (normalize, denoise) and batch processing options.

---
Updated to reflect recent changes and migration behavior.
- If splits are missing or too frequent, try adjusting `--min_silence` and `--silence_thresh`.

- Use the `--analyze` flag to get suggested parameters for your specific audio files.
