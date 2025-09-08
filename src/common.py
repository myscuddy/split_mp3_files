import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext

class scriptClass:
    def __init__(self, lt=None):
        self._log_text=lt

    def get_log_text(self):
        return self._log_text
    
    def set_log_text(self, stst:scrolledtext.ScrolledText):
        self._log_text = stst

def log(msg, sc):
    lt=sc.get_log_text()
    lt.config(state=tk.NORMAL)
    lt.insert(tk.END, msg + '\n')
    lt.yview(tk.END)
    lt.config(state=tk.DISABLED)

