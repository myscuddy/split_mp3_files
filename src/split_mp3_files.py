import sys
import logging
import argparse
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext
import os
import threading
import traceback

from split_mp3 import split_mp3_on_silence, split_mp3_by_time, split_mp3_by_silence_intervals, analyze_silence
import common as cm
import run_repo as rr

VALID_MODES = ["Silence", "Time"]
class SplitConstants:
    MIN_SILENCE = 1000
    SILENCE_THRESH = -40
    CHUNK_LENGTH = 60000

def run_split(split_context, files, outdir, mode, min_silence=1000, silence_thresh=-40, chunk_length=60000, silence_offset=-16, adaptive=False, use_silence_intervals=False, bitrate_kbps=256, vbr_quality=None, silence_padding_ms=3000, use_logger=False):
    if use_logger:
        logger = logging.getLogger("split_mp3_cli")
        logger.info("Starting split operation...")
    else:
        cm.log("Starting split operation...", split_context)

    # Log full parameter set before starting
    params = {
        "mode": mode,
        "min_silence": min_silence,
        "silence_thresh": silence_thresh,
        "chunk_length": chunk_length,
        "silence_offset": silence_offset,
        "adaptive": adaptive,
        "use_silence_intervals": use_silence_intervals,
        "bitrate_kbps": bitrate_kbps,
        "vbr_quality": vbr_quality,
        "silence_padding_ms": silence_padding_ms,
    }
    if use_logger:
        logger.info(f"Parameters: {params}")
    else:
        cm.log(f"Parameters: {params}", split_context)

    if not files or not files[0]:
        msg = "No files selected."
        if use_logger:
            logger.error(msg)
        else:
            messagebox.showerror("Error", msg)
            cm.log(msg, split_context)
        return
    if not outdir:
        msg = "No output directory selected."
        if use_logger:
            logger.error(msg)
        else:
            messagebox.showerror("Error", msg)
            cm.log(msg, split_context)
        return

    try:
        if mode == "Silence":
            for f in files:
                msg = f"Splitting {os.path.basename(f)} on silence..."
                if use_logger:
                    logger.info(msg)
                else:
                    cm.log(msg, split_context)
                # Save the run options for this source file before processing
                try:
                    rr.save_run(f, params)
                except Exception:
                    pass
                if adaptive:
                    output_files = split_mp3_on_silence(f, outdir, min_silence, silence_thresh=None, silence_offset=silence_offset, bitrate_kbps=bitrate_kbps, vbr_quality=vbr_quality, silence_padding_ms=silence_padding_ms, sc=split_context)
                else:
                    output_files = split_mp3_on_silence(f, outdir, min_silence, silence_thresh, bitrate_kbps=bitrate_kbps, vbr_quality=vbr_quality, silence_padding_ms=silence_padding_ms, sc=split_context)
                msg = f"Created {len(output_files)} chunks for {os.path.basename(f)}"
                if use_logger:
                    logger.info(msg)
                else:
                    cm.log(msg, split_context)
        else:
            for f in files:
                msg = f"Splitting {os.path.basename(f)} by time interval..."
                if use_logger:
                    logger.info(msg)
                else:
                    cm.log(msg, split_context)
                # Save the run options for this source file before processing
                try:
                    rr.save_run(f, params)
                except Exception:
                    pass
                if use_silence_intervals:
                    output_files = split_mp3_by_silence_intervals(f, out_dir=outdir, min_silence_len=min_silence, silence_thresh=(None if adaptive else silence_thresh), silence_offset=silence_offset, bitrate_kbps=bitrate_kbps, vbr_quality=vbr_quality, silence_padding_ms=silence_padding_ms, sc=split_context)
                else:
                    output_files = split_mp3_by_time(f, outdir, chunk_length, bitrate_kbps=bitrate_kbps, vbr_quality=vbr_quality, silence_padding_ms=silence_padding_ms, sc=split_context)
                msg = f"Created {len(output_files)} chunks for {os.path.basename(f)}"
                if use_logger:
                    logger.info(msg)
                else:
                    cm.log(msg, split_context)
        msg = "Splitting completed successfully."
        if use_logger:
            logger.info(msg)
        else:
            messagebox.showinfo("Success", "MP3 splitting completed!")
            cm.log(msg, split_context)
    except Exception as e:
        tb = traceback.format_exc()
        msg = f"Error: {e}\n{tb}"
        if use_logger:
            logger.error(msg)
        else:
            cm.log(msg, split_context)
            messagebox.showerror("Error", f"An error occurred:\n{e}")


def start_gui(runs_dir=None):
    """Create and run the Tkinter GUI. This function wraps the existing UI code so it can
    be started from the CLI with `--gui` or by running the script without args.
    
    Args:
        runs_dir: Optional directory where run configuration is stored.
                 If provided, this is used instead of the default location.
    """
    # Set runs directory if provided
    if runs_dir:
        rr.set_runs_dir(runs_dir)
    
    def select_files():
        files = filedialog.askopenfilenames(filetypes=[("MP3 Files", "*.mp3")])
        if files:
            files_var.set('\n'.join(files))
            try:
                update_history_list()
            except Exception:
                pass

    def select_output_dir():
        directory = filedialog.askdirectory()
        if directory:
            outdir_var.set(directory)

    def run_split_ui(sc: cm.scriptClass):
        files = files_var.get().strip().split('\n') if files_var.get().strip() else None
        outdir = outdir_var.get().strip()
        mode = mode_var.get()
        min_silence = int(min_silence_var.get()) if min_silence_var.get().strip() else SplitConstants.MIN_SILENCE
        # If adaptive checkbox is set, pass silence_thresh as None so run_split computes it
        adaptive = adaptive_var.get()
        silence_offset = int(silence_offset_var.get()) if silence_offset_var.get().strip() else -16
        silence_thresh = None if adaptive else (int(silence_thresh_var.get()) if silence_thresh_var.get().strip() else SplitConstants.SILENCE_THRESH)
        chunk_length = int(chunk_length_var.get()) if chunk_length_var.get().strip() else SplitConstants.CHUNK_LENGTH
        use_silence_intervals = use_silence_intervals_var.get() if 'use_silence_intervals_var' in globals() or 'use_silence_intervals_var' in locals() else False
        bitrate_kbps = int(bitrate_var.get()) if bitrate_var.get().strip() else 256
        vbr_quality = int(vbr_quality_var.get()) if vbr_quality_var.get().strip() else None
        silence_padding_ms = int(silence_padding_var.get()) if silence_padding_var.get().strip() else 3000
        run_split(sc, files, outdir, mode, min_silence, silence_thresh, chunk_length, silence_offset=silence_offset, adaptive=adaptive, use_silence_intervals=use_silence_intervals, bitrate_kbps=bitrate_kbps, vbr_quality=vbr_quality, silence_padding_ms=silence_padding_ms, use_logger=False)

    def start_split_thread():
        # Before starting: save current options to repo and insert a history entry at top
        try:
            files = files_var.get().strip().split('\n') if files_var.get().strip() else None
            if files and files[0]:
                # compute the same params as run_split_ui
                mode = mode_var.get()
                min_silence = int(min_silence_var.get()) if min_silence_var.get().strip() else SplitConstants.MIN_SILENCE
                adaptive = adaptive_var.get()
                silence_offset = int(silence_offset_var.get()) if silence_offset_var.get().strip() else -16
                silence_thresh = None if adaptive else (int(silence_thresh_var.get()) if silence_thresh_var.get().strip() else SplitConstants.SILENCE_THRESH)
                chunk_length = int(chunk_length_var.get()) if chunk_length_var.get().strip() else SplitConstants.CHUNK_LENGTH
                use_silence_intervals = use_silence_intervals_var.get()
                bitrate_kbps = int(bitrate_var.get()) if bitrate_var.get().strip() else 256
                vbr_quality = int(vbr_quality_var.get()) if vbr_quality_var.get().strip() else None
                silence_padding_ms = int(silence_padding_var.get()) if silence_padding_var.get().strip() else 3000

                params = {
                    "mode": mode,
                    "min_silence": min_silence,
                    "silence_thresh": silence_thresh,
                    "chunk_length": chunk_length,
                    "silence_offset": silence_offset,
                    "adaptive": adaptive,
                    "use_silence_intervals": use_silence_intervals,
                    "bitrate_kbps": bitrate_kbps,
                    "vbr_quality": vbr_quality,
                    "silence_padding_ms": silence_padding_ms,
                }

                # Save run for each selected file; update GUI history for first file
                saved_repo_paths = []
                for idx, f in enumerate(files):
                    try:
                        rr.save_run(f, params)
                        repo_path = rr.get_repo_file_for_path(f)
                        saved_repo_paths.append(repo_path)
                        # for first file, update history listbox immediately
                        if idx == 0:
                            runs = rr.load_runs(f)
                            if runs:
                                r = runs[0]
                                ts = r.get('timestamp', '')
                                opts = r.get('options', {})
                                summary = f"{ts} — mode={opts.get('mode')} bitrate={opts.get('bitrate_kbps')} vbr={opts.get('vbr_quality')} pad={opts.get('silence_padding_ms')}"
                                history_listbox.insert(0, summary)
                                history_runs.insert(0, r)
                    except Exception:
                        pass
        except Exception:
            saved_repo_paths = []

        # Disable the button and show an indeterminate progress bar while work runs
        split_btn.config(state=tk.DISABLED)
        status_var.set("Working...")
        progressbar.start(10)

        def worker():
            try:
                run_split_ui(sc)
            finally:
                # Schedule UI updates on the main thread when done
                def on_done():
                    progressbar.stop()
                    status_var.set("")
                    split_btn.config(state=tk.NORMAL)
                    # Log repository file paths where runs were recorded
                    try:
                        if saved_repo_paths:
                            for p in saved_repo_paths:
                                cm.log(f"Run configuration written to: {p}", sc)
                    except Exception:
                        pass
                root.after(0, on_done)

        threading.Thread(target=worker, daemon=True).start()

    root = tk.Tk()
    root.title("MP3 Splitter")
    root.geometry("620x540")

    files_var = tk.StringVar()
    outdir_var = tk.StringVar()
    mode_var = tk.StringVar(value="Silence")
    min_silence_var = tk.StringVar(value=str(SplitConstants.MIN_SILENCE))  # Default 1000 ms
    silence_thresh_var = tk.StringVar(value=str(SplitConstants.SILENCE_THRESH))  # Default -40 dBFS
    silence_offset_var = tk.StringVar(value=str(-16))
    adaptive_var = tk.BooleanVar(value=False)
    use_silence_intervals_var = tk.BooleanVar(value=False)
    chunk_length_var = tk.StringVar(value=str(SplitConstants.CHUNK_LENGTH))  # Default 60000 ms
    # Output options
    bitrate_var = tk.StringVar(value=str(256))
    vbr_quality_var = tk.StringVar(value="")
    silence_padding_var = tk.StringVar(value=str(3000))

    tk.Label(root, text="Select MP3 Files:").pack(anchor="w", padx=10, pady=(10,0))
    tk.Button(root, text="Choose Files", command=select_files).pack(anchor="w", padx=10)
    tk.Label(root, textvariable=files_var, wraplength=580, justify="left", bg="#eee", anchor="w").pack(fill="x", padx=10, pady=(0,10))

    # Recent runs list for the selected source file
    history_frame = tk.Frame(root)
    tk.Label(history_frame, text="Recent runs for selected file:").pack(anchor="w")
    history_listbox = tk.Listbox(history_frame, height=6)
    history_scroll = tk.Scrollbar(history_frame, orient=tk.VERTICAL, command=history_listbox.yview)
    history_listbox.config(yscrollcommand=history_scroll.set)
    history_listbox.pack(side="left", fill="both", expand=True)
    history_scroll.pack(side="right", fill="y")
    history_frame.pack(fill="x", padx=10, pady=(0,10))
    history_runs = []

    def update_history_list():
        nonlocal history_runs
        history_listbox.delete(0, tk.END)
        history_runs = []
        files = files_var.get().strip().split('\n') if files_var.get().strip() else None
        if not files or not files[0]:
            return
        f = files[0]
        try:
            runs = rr.load_runs(f)
        except Exception:
            runs = []
        for i, r in enumerate(runs):
            ts = r.get('timestamp', '')
            opts = r.get('options', {})
            summary = f"{ts} — mode={opts.get('mode')} bitrate={opts.get('bitrate_kbps')} vbr={opts.get('vbr_quality')} pad={opts.get('silence_padding_ms')}"
            history_listbox.insert(tk.END, summary)
            history_runs.append(r)

    def apply_selected_run():
        sel = history_listbox.curselection()
        if not sel:
            messagebox.showinfo("Info", "Select a recent run to apply its options.")
            return
        run_entry = history_runs[sel[0]]
        opts = run_entry.get('options', {})
        # populate GUI options
        mode_var.set(opts.get('mode', 'Silence'))
        min_silence_var.set(str(opts.get('min_silence', SplitConstants.MIN_SILENCE)))
        if opts.get('silence_thresh') is None:
            silence_thresh_var.set('')
        else:
            silence_thresh_var.set(str(opts.get('silence_thresh', SplitConstants.SILENCE_THRESH)))
        adaptive_var.set(bool(opts.get('adaptive', False)))
        silence_offset_var.set(str(opts.get('silence_offset', -16)))
        chunk_length_var.set(str(opts.get('chunk_length', SplitConstants.CHUNK_LENGTH)))
        use_silence_intervals_var.set(bool(opts.get('use_silence_intervals', False)))
        bitrate_var.set(str(opts.get('bitrate_kbps', 256)))
        vbr_quality_var.set(str(opts.get('vbr_quality') if opts.get('vbr_quality') is not None else ""))
        silence_padding_var.set(str(opts.get('silence_padding_ms', 3000)))
        update_options()

    def run_selected_and_start():
        apply_selected_run()
        start_split_thread()

    btn_frame = tk.Frame(root)
    tk.Button(btn_frame, text="Apply Selected Run", command=apply_selected_run).pack(side="left", padx=4)
    tk.Button(btn_frame, text="Run Selected Run", command=run_selected_and_start).pack(side="left", padx=4)
    btn_frame.pack(anchor="w", padx=10, pady=(0,10))

    tk.Label(root, text="Select Output Directory:").pack(anchor="w", padx=10)
    tk.Button(root, text="Choose Directory", command=select_output_dir).pack(anchor="w", padx=10)
    tk.Label(root, textvariable=outdir_var, bg="#eee", anchor="w").pack(fill="x", padx=10, pady=(0,10))

    tk.Label(root, text="Split Mode:").pack(anchor="w", padx=10)
    ttk.Radiobutton(root, text="Split on Silence", variable=mode_var, value="Silence").pack(anchor="w", padx=20)
    ttk.Radiobutton(root, text="Split by Time Interval", variable=mode_var, value="Time").pack(anchor="w", padx=20)

    frame = tk.Frame(root)
    frame.pack(fill="x", padx=10, pady=10)

    def update_options(*_):
        if mode_var.get() == "Silence":
            silence_frame.pack(fill="x")
            time_frame.forget()
        else:
            time_frame.pack(fill="x")
            silence_frame.forget()

    mode_var.trace("w", update_options)

    silence_frame = tk.Frame(frame)
    tk.Label(silence_frame, text="Min Silence Length (ms):").grid(row=0, column=0, sticky="w", padx=2)
    tk.Entry(silence_frame, textvariable=min_silence_var, width=10).grid(row=0, column=1, padx=2)
    tk.Label(silence_frame, text="Silence Threshold (dBFS):").grid(row=1, column=0, sticky="w", padx=2)
    tk.Entry(silence_frame, textvariable=silence_thresh_var, width=10).grid(row=1, column=1, padx=2)
    tk.Checkbutton(silence_frame, text="Adaptive threshold (per-file)", variable=adaptive_var).grid(row=2, column=0, columnspan=2, sticky="w", pady=(6,0))
    tk.Label(silence_frame, text="Silence offset (dB):").grid(row=3, column=0, sticky="w", padx=2)
    tk.Entry(silence_frame, textvariable=silence_offset_var, width=10).grid(row=3, column=1, padx=2)
    silence_frame.pack(fill="x")
    # Analyze button to suggest min_silence and threshold
    def on_analyze_button():
        files = files_var.get().strip().split('\n') if files_var.get().strip() else None
        if not files or not files[0]:
            messagebox.showerror("Error", "Please select an input MP3 file to analyze.")
            return
        # analyze first file
        f = files[0]
        # run analysis in background
        def do_analysis():
            try:
                result = analyze_silence(f, min_silence_search_ms=200, silence_offset=int(silence_offset_var.get()) if silence_offset_var.get().strip() else -16, sc=sc)
                def finish():
                    # Show analysis result and ask if user wants to update GUI options
                    message = f"Detected {result['count_silences']} silences.\nSuggested min_silence={result.get('suggested_min_silence_ms')} ms\nSuggested silence_thresh={result.get('suggested_silence_thresh')} dBFS\n\nWould you like to update the GUI options with these values?"
                    response = messagebox.askyesno("Analysis Complete", message)
                    if response:
                        # populate GUI fields with suggested values
                        min_silence_var.set(str(result.get('suggested_min_silence_ms', SplitConstants.MIN_SILENCE)))
                        silence_thresh_var.set(str(result.get('suggested_silence_thresh', SplitConstants.SILENCE_THRESH)))
                root.after(0, finish)
            except Exception as e:
                def fail():
                    messagebox.showerror("Analysis Error", f"Error during analysis: {e}")
                root.after(0, fail)

        progressbar.start(10)
        threading.Thread(target=lambda: (do_analysis(), root.after(0, lambda: progressbar.stop())), daemon=True).start()

    time_frame = tk.Frame(frame)
    tk.Label(time_frame, text="Chunk Length (ms):").grid(row=0, column=0, sticky="w", padx=2)
    tk.Entry(time_frame, textvariable=chunk_length_var, width=10).grid(row=0, column=1, padx=2)
    tk.Checkbutton(time_frame, text="Detect songs by silence (analyze first)", variable=use_silence_intervals_var).grid(row=1, column=0, columnspan=2, sticky="w", pady=(6,0))


    # Output options frame (bitrate / vbr / padding)
    out_frame = tk.Frame(frame)
    tk.Label(out_frame, text="Bitrate (kbps):").grid(row=0, column=0, sticky="w", padx=2)
    bitrate_combo = ttk.Combobox(out_frame, values=("64","128","192","256","320"), textvariable=bitrate_var, width=8, state="readonly")
    bitrate_combo.grid(row=0, column=1, padx=2)
    # set default selection to 256
    try:
        bitrate_combo.current(["64","128","192","256","320"].index(bitrate_var.get()))
    except Exception:
        bitrate_combo.set("256")
    tk.Label(out_frame, text="VBR quality (0-9, optional):").grid(row=1, column=0, sticky="w", padx=2)
    tk.Entry(out_frame, textvariable=vbr_quality_var, width=10).grid(row=1, column=1, padx=2)
    tk.Label(out_frame, text="Silence padding (ms):").grid(row=2, column=0, sticky="w", padx=2)
    tk.Entry(out_frame, textvariable=silence_padding_var, width=10).grid(row=2, column=1, padx=2)
    out_frame.pack(fill="x", pady=(6,0))

    button_frame = tk.Frame(root)
    tk.Button(button_frame, text="Analyze File", command=on_analyze_button).pack(side="left", padx=4)
    split_btn = tk.Button(button_frame, text="Start Splitting", command=start_split_thread, bg="#28a745", fg="white")
    split_btn.pack(side="left", padx=4)
    button_frame.pack(pady=10)

    # Progress indicator and status
    progressbar = ttk.Progressbar(root, mode="indeterminate", length=560)
    progressbar.pack(padx=10, pady=(0,6))
    status_var = tk.StringVar(value="")
    tk.Label(root, textvariable=status_var, fg="#333").pack(anchor="w", padx=12)

    tk.Label(root, text="Log Output:").pack(anchor="w", padx=10)

    sc = cm.scriptClass()
    sc.set_log_text(scrolledtext.ScrolledText(root, height=10, state=tk.DISABLED, wrap='word', bg="#f7f7f7"))
    sc1 = sc.get_log_text()
    sc1.pack(fill="both", expand=True, padx=10, pady=(0,10))

    tk.Label(root, text="Note: Requires ffmpeg installed and available in PATH.", fg="gray").pack(side="bottom", pady=5)

    update_options()

    root.mainloop()

def main_cli():
    parser = argparse.ArgumentParser(description="MP3 Splitter CLI")
    parser.add_argument("--mode", choices=VALID_MODES, help="Splitting mode: Silence or Time")
    parser.add_argument("--input_files", nargs="+", help="Input MP3 file(s)")
    parser.add_argument("--output_dir", help="Output directory")
    parser.add_argument("--runs_dir", help="Directory where run configuration is stored (defaults to $HOME/.config/split_mp3_files on Linux/macOS, %%APPDATA%%\\split_mp3_files on Windows)")
    parser.add_argument("--gui", action="store_true", help="Start the graphical UI instead of running CLI mode")
    parser.add_argument("--min_silence", type=int, default=1000, help="Minimum silence length in ms (Silence mode)")
    parser.add_argument("--silence_thresh", type=int, default=-40, help="Silence threshold in dBFS (Silence mode). If omitted together with --adaptive, adaptive mode will be used.")
    parser.add_argument("--adaptive", action="store_true", help="Compute silence threshold relative to each file's overall loudness (uses --silence_offset)")
    parser.add_argument("--silence_offset", type=int, default=-16, help="dB offset below file dBFS when --adaptive is used (negative number, e.g. -16)")
    parser.add_argument("--use_silence_intervals", action="store_true", help="When in Time mode, detect silence intervals and split into tracks instead of fixed-length chunks")
    parser.add_argument("--chunk_length", type=int, default=60000, help="Chunk length in ms (Time mode)")
    parser.add_argument("--bitrate", type=int, default=256, choices=[64,128,192,256,320], help="Output bitrate in kbps (choices: 64, 128, 192, 256, 320). Default 256")
    parser.add_argument("--vbr_quality", type=int, default=None, help="Optional VBR quality (0-9) - lower is better; when set, overrides --bitrate")
    parser.add_argument("--silence_padding", type=int, default=3000, help="Milliseconds of silence to add to start/end of each chunk (default 3000)")
    parser.add_argument("--analyze", action="store_true", help="Analyze input file(s) for silence statistics and print suggested parameters")
    parser.add_argument("--apply_analysis", action="store_true", help="Analyze the first input file and apply suggested min_silence/silence_thresh when splitting")

    args = parser.parse_args()
    
    # Set runs directory if provided
    if args.runs_dir:
        rr.set_runs_dir(args.runs_dir)
    
    # If the user requested the GUI, start it and exit
    if args.gui:
        start_gui()
        return

    # Validate required CLI parameters when not running the GUI
    if not args.input_files:
        print("Missing --input_files; provide one or more MP3 files or use --gui to open the UI.")
        sys.exit(1)
    for f in args.input_files:
        if not os.path.isfile(f):
            print(f"Input file not found: {f}")
            sys.exit(1)
    if not args.output_dir:
        print("Missing --output_dir; provide an output directory or use --gui to open the UI.")
        sys.exit(1)
    if not os.path.isdir(args.output_dir):
        try:
            os.makedirs(args.output_dir, exist_ok=True)
        except Exception as e:
            print(f"Could not create output directory: {args.output_dir}\n{e}")
            sys.exit(1)

    logging.basicConfig(level=logging.INFO)
    # If analysis-only requested, run analysis and print results
    if args.analyze:
        for f in args.input_files:
            if not os.path.isfile(f):
                print(f"Input file not found: {f}")
                continue
            res = analyze_silence(f, min_silence_search_ms=200, silence_offset=args.silence_offset)
            print(f"Analysis for {f}:")
            print(f"  audio dBFS: {res['audio_dBFS']:.1f} dBFS")
            print(f"  detected silences: {res['count_silences']}")
            print(f"  median silence (ms): {res.get('median_silence_ms',0)}")
            print(f"  p75 silence (ms): {res.get('p75_silence_ms',0)}")
            print(f"  suggested min_silence (ms): {res.get('suggested_min_silence_ms')}")
            print(f"  suggested silence_thresh (dBFS): {res.get('suggested_silence_thresh')}")
        if not args.apply_analysis:
            return

    run_split(
        None,
        args.input_files,
        args.output_dir,
        args.mode,
        args.min_silence,
        args.silence_thresh,
        args.chunk_length,
        silence_offset=args.silence_offset,
        adaptive=args.adaptive,
        use_silence_intervals=args.use_silence_intervals,
        bitrate_kbps=args.bitrate,
        vbr_quality=args.vbr_quality,
        silence_padding_ms=args.silence_padding,
        use_logger=True,
    )

if __name__ == "__main__":
    # If any named argument is present, run CLI mode
    if any(arg.startswith("--") for arg in sys.argv[1:]):
        main_cli()
    else:
        # No-arg run — start the GUI
        start_gui()