import os
import logging
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext
from datetime import datetime
import run_repo as rr


class scriptClass:
    def __init__(self, lt=None):
        self._log_text = lt

    def get_log_text(self):
        return self._log_text

    def set_log_text(self, stst: scrolledtext.ScrolledText):
        self._log_text = stst


def log(msg, sc, logger=None):
    # write to the GUI log widget if available
    try:
        lt = sc.get_log_text()
        lt.config(state=tk.NORMAL)
        lt.insert(tk.END, msg + '\n')
        lt.yview(tk.END)
        lt.config(state=tk.DISABLED)
    except Exception:
        pass

    # append the same message to a persistent log file in the runs repo dir
    try:
        # If a logger is provided, use it
        if logger:
            try:
                logger.info(msg)
                return
            except Exception:
                # Fall through to file-backed logging on failure
                pass

        # Fallback: ensure a file-based logger writing to the repo log exists
        repo_file = rr.get_repo_file_for_path("")
        repo_dir = os.path.dirname(repo_file)
        os.makedirs(repo_dir, exist_ok=True)
        log_path = os.path.join(repo_dir, "split_mp3.log")

        file_logger = logging.getLogger("split_mp3.filelogger")
        abs_log_path = os.path.abspath(log_path)
        needs_handler = True
        for h in file_logger.handlers:
            try:
                if isinstance(h, logging.FileHandler) and os.path.abspath(getattr(h, "baseFilename", "")) == abs_log_path:
                    needs_handler = False
                    break
            except Exception:
                continue
        if needs_handler:
            fh = logging.FileHandler(log_path, encoding="utf-8")
            fh.setLevel(logging.INFO)
            fh.setFormatter(logging.Formatter("%(asctime)sZ - %(levelname)s - %(message)s"))
            file_logger.addHandler(fh)
            file_logger.setLevel(logging.INFO)

        file_logger.info(msg)
    except Exception:
        pass

