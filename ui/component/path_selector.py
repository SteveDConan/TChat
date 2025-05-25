import tkinter as tk
from tkinter import filedialog

class PathSelectorFrame(tk.Frame):
    """
    Component chọn đường dẫn thư mục (Folder Picker)
    """
    def __init__(self, master, lang):
        super().__init__(master)
        self.lang = lang
        self.path_var = tk.StringVar()

        tk.Label(self, text=lang["telegram_path_label"]).pack(side=tk.LEFT, padx=5)
        self.entry = tk.Entry(self, textvariable=self.path_var, width=50)
        self.entry.pack(side=tk.LEFT, padx=5)
        btn_browse = tk.Button(self, text=lang["choose_folder"], command=self.browse_folder)
        btn_browse.pack(side=tk.LEFT, padx=5)

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.path_var.set(folder)

    def get_path(self):
        return self.path_var.get()

    def set_path(self, value):
        self.path_var.set(value)
