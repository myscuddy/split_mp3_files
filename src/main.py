import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext
import os
import threading
import traceback

from split_mp3 import split_mp3_on_silence, split_mp3_by_time
import common as cm

def select_files():
    files = filedialog.askopenfilenames(filetypes=[("MP3 Files", "*.mp3")])
    if files:
        files_var.set('\n'.join(files))

def select_output_dir():
    dirz = filedialog.askdirectory()
    if dirz:
        outdir_var.set(dirz)

def run_split(sc:cm.scriptClass):
    files = files_var.get().strip().split('\n')
    outdir = outdir_var.get().strip()
    mode = mode_var.get()
    cm.log("Starting split operation...",sc, None)

    if not files or not files[0]:
        messagebox.showerror("Error", "Please select one or more MP3 files.")
        cm.log("No files selected.",sc, None)
        return
    if not outdir:
        messagebox.showerror("Error", "Please select an output directory.")
        cm.log("No output directory selected.",sc, None)
        return

    try:
        if mode == "Silence":
            min_silence = int(min_silence_var.get())
            silence_thresh = int(silence_thresh_var.get())
            for f in files:
                cm.log(f"Splitting {os.path.basename(f)} on silence...",sc, None)
                output_files = split_mp3_on_silence(f, outdir, min_silence, silence_thresh, sc=sc)
                cm.log(f"Created {len(output_files)} chunks for {os.path.basename(f)}",sc, None)
        else:
            chunk_length = int(chunk_length_var.get())
            for f in files:
                cm.log(f"Splitting {os.path.basename(f)} by time interval...",sc, None)
                output_files = split_mp3_by_time(f, outdir, chunk_length, sc=sc)
                cm.log(f"Created {len(output_files)} chunks for {os.path.basename(f)}",sc, None)
        messagebox.showinfo("Success", "MP3 splitting completed!")
        cm.log("Splitting completed successfully.",sc, None)
    except Exception as e:
        tb = traceback.format_exc()
        cm.log(f"Error: {e}\n{tb}",sc, None)
        messagebox.showerror("Error", f"An error occurred:\n{e}")

def start_split_thread():
    # Disable UI to prevent multiple runs
    split_btn.config(state=tk.DISABLED)
    def wrapper():
        try:
            run_split(sc)
        finally:
            split_btn.config(state=tk.NORMAL)
    threading.Thread(target=wrapper, daemon=True).start()

root = tk.Tk()
root.title("MP3 Splitter")
root.geometry("600x500")

files_var = tk.StringVar()
outdir_var = tk.StringVar()
mode_var = tk.StringVar(value="Silence")
min_silence_var = tk.StringVar(value="1000")
silence_thresh_var = tk.StringVar(value="-40")
chunk_length_var = tk.StringVar(value="60000")

tk.Label(root, text="Select MP3 Files:").pack(anchor="w", padx=10, pady=(10,0))
tk.Button(root, text="Choose Files", command=select_files).pack(anchor="w", padx=10)
tk.Label(root, textvariable=files_var, wraplength=560, justify="left", bg="#eee", anchor="w").pack(fill="x", padx=10, pady=(0,10))

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
silence_frame.pack(fill="x")

time_frame = tk.Frame(frame)
tk.Label(time_frame, text="Chunk Length (ms):").grid(row=0, column=0, sticky="w", padx=2)
tk.Entry(time_frame, textvariable=chunk_length_var, width=10).grid(row=0, column=1, padx=2)

split_btn = tk.Button(root, text="Start Splitting", command=start_split_thread, bg="#28a745", fg="white")
split_btn.pack(pady=10)

tk.Label(root, text="Log Output:").pack(anchor="w", padx=10)

sc=cm.scriptClass()
sc.set_log_text(scrolledtext.ScrolledText(root, height=10, state=tk.DISABLED, wrap='word', bg="#f7f7f7"))
sc1=sc.get_log_text()
sc1.pack(fill="both", expand=True, padx=10, pady=(0,10))

tk.Label(root, text="Note: Requires ffmpeg installed and available in PATH.", fg="gray").pack(side="bottom", pady=5)

update_options()

root.mainloop()
