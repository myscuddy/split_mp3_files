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

You can override the default location with the `--runs_dir` parameter:

```bash
python src/split_mp3_files.py --gui --runs_dir /custom/path
```

## CLI Usage

Run the CLI script at `src/split_mp3_files.py` with the following options:

- `--mode` : Splitting mode. Choices: `Silence` or `Time`. (required for non-GUI CLI)
- `--input_files` : One or more input MP3 file paths. (required for non-GUI CLI)
- `--output_dir` : Output directory for chunks. (required for non-GUI CLI)
- `--runs_dir` : Directory to store run configuration (defaults to `~/.config/split_mp3_files`)
- `--gui` : Start the graphical UI instead of running the CLI.
- `--min_silence` : Minimum silence length in milliseconds for `Silence` mode. Default: `1000` (1 second).
- `--silence_thresh` : Silence threshold in dBFS for `Silence` mode. Default: `-40`.
- `--adaptive` : Enable adaptive threshold computed per-file (uses file dBFS plus `--silence_offset`).
- `--silence_offset` : dB offset applied to file dBFS when `--adaptive` is used. Default: `-16`.
- `--use_silence_intervals` : When using `Time` mode, analyze the file first and split tracks by detected long silence intervals (useful when the source is an album or compilation of songs).
- `--chunk_length` : Chunk length in milliseconds for `Time` mode. Default: `60000` (60 seconds).
- `--bitrate` : Output bitrate in kbps. Choices: `64`, `128`, `192`, `256`, `320`. Default: `256`.
- `--vbr_quality` : Optional VBR quality (0-9, lower is better). When set, overrides `--bitrate`.
- `--silence_padding` : Milliseconds of silence to add to start/end of each chunk. Default: `3000`.
- `--analyze` : Analyze input file(s) for silence statistics and print suggested parameters (does not split).
- `--apply_analysis` : Analyze the first input file and apply suggested parameters when splitting.

Notes about `--use_silence_intervals`:
- This option analyzes silence ranges in the file to find likely song boundaries and exports segments between those silences. It is slower than fixed-time splitting but produces one file per detected track.
- Combine with `--adaptive`/`--silence_offset` to let the detector compute a per-file threshold.

Notes:
- `--silence_thresh` controls how quiet audio must be to count as silence. For quieter recordings use a higher (less negative) value; for louder/clean recordings use a lower (more negative) value.
- `--min_silence` controls minimum duration required to be considered a split point.
- `ffmpeg` must be installed at the system level (e.g., `sudo apt install ffmpeg` on Debian/Ubuntu).

### Examples

Split on silence (uses defaults for silence settings):

```bash
python src/split_mp3_files.py \
	--mode Silence \
	--input_files /path/to/episode.mp3 /path/to/another.mp3 \
	--output_dir ./out_chunks
```

Split on silence with tuned parameters:

```bash
python src/split_mp3_files.py \
	--mode Silence \
	--input_files /path/to/episode.mp3 \
	--output_dir ./out_chunks \
	--min_silence 800 \
	--silence_thresh -35
```

Split by fixed time intervals (30-second chunks):

```bash
python src/split_mp3_files.py \
	--mode Time \
	--input_files /path/to/episode.mp3 \
	--output_dir ./out_chunks \
	--chunk_length 30000
```

Split by analyzing silence intervals first (detect tracks between songs):

```bash
python src/split_mp3_files.py \
	--mode Time \
	--input_files /path/to/album_mix.mp3 \
	--output_dir ./out_tracks \
	--use_silence_intervals
```

Analyze a file to get suggested parameters:

```bash
python src/split_mp3_files.py \
	--analyze \
	--input_files /path/to/episode.mp3
```

Analyze and apply suggested settings:

```bash
python src/split_mp3_files.py \
	--apply_analysis \
	--mode Silence \
	--input_files /path/to/episode.mp3 \
	--output_dir ./out_chunks
```

Use custom configuration directory:

```bash
python src/split_mp3_files.py --gui --runs_dir /media/config/split_mp3
```

Open the GUI instead of using the CLI:

```bash
python src/split_mp3_files.py --gui
```

## GUI

There is a simple Tkinter GUI available by running the script without CLI flags or with `--gui`. The GUI provides:

- File selection for input MP3s and output directory
- Recent runs history with one-click application
- All CLI options exposed as form fields
- Real-time log output pane
- Progress indicator during splitting
- Analyze button to automatically suggest optimal parameters

## Tuning tips (silence splitting reliability)

- If splits are missing or too frequent, try adjusting `--min_silence` and `--silence_thresh`.
- Use the `--analyze` flag to get suggested parameters for your specific audio files.
- Consider converting stereo to mono or normalizing audio before splitting for more consistent detection.
- The GUI "Analyze File" button provides interactive parameter suggestions.

## Version History

### v1.1.0 (2026-01-25)
- **New**: Single configuration file (`runs.json`) for all sources instead of per-file hashes
- **New**: Configurable runs directory via `--runs_dir` parameter with smart defaults
- **New**: GUI history list with "Apply Selected Run" and "Run Selected Run" buttons
- **New**: Analysis feature to suggest optimal split parameters
- **New**: Button layout improvements (Analyze and Start Splitting on same line)
- **Enhanced**: Better bitrate defaults (256 kbps) with full range support (64-320)
- **Enhanced**: Cross-platform configuration storage support (Linux/macOS/Windows)
- **Fixed**: Improved error handling for config directory creation

### v1.0.0 (Initial Release)
- Silence detection splitting mode
- Time-based splitting mode
- CLI and GUI interfaces
- Basic configuration storage

## Contributing / Next improvements

- Add unit/integration tests and sample audio files to reproduce edge cases.
- Advanced audio preprocessing options (normalize, denoise).
- Batch processing improvements.
- Dark mode for GUI.

---
Updated with latest features and improvements (v1.1.0)

