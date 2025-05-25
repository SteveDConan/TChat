import tkinter as tk
from tkinter import ttk, messagebox

class CheckLiveWindow(tk.Toplevel):
    """
    Cửa sổ check live trạng thái tài khoản (so sánh ảnh, xác nhận...).
    """
    def __init__(self, master, lang, check_live_status, on_start, on_pause, on_confirm, on_copy_inactive, on_delete_inactive, on_copy_table):
        super().__init__(master)
        self.title(lang["check_live_title"])
        self.lang = lang
        self.check_live_status = check_live_status

        # Setup các widget
        self.geometry("1200x500")
        size_frame = tk.Frame(self)
        size_frame.pack(pady=5)
        tk.Label(size_frame, text="Window Width:").grid(row=0, column=0, padx=5)
        self.entry_width = tk.Entry(size_frame, width=6)
        self.entry_width.grid(row=0, column=1, padx=5)
        tk.Label(size_frame, text="Window Height:").grid(row=0, column=2, padx=5)
        self.entry_height = tk.Entry(size_frame, width=6)
        self.entry_height.grid(row=0, column=3, padx=5)

        # Bảng trạng thái
        columns = ("stt", "tdata", "check_status", "live_status")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=15)
        for col, text in zip(columns, [lang["stt"], "TData", lang["check_status"], lang["live_status"]]):
            self.tree.heading(col, text=text)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Nút chức năng
        frame_buttons = tk.Frame(self)
        frame_buttons.pack(pady=5)
        self.btn_start = tk.Button(frame_buttons, text=lang["start"], command=on_start, width=20)
        self.btn_pause = tk.Button(frame_buttons, text=lang["pause"], command=on_pause, width=20, state=tk.DISABLED)
        self.btn_confirm = tk.Button(frame_buttons, text=lang["confirm"], command=on_confirm, width=20)
        self.btn_copy_inactive = tk.Button(frame_buttons, text=lang["copy_inactive"], command=on_copy_inactive, width=25, state=tk.DISABLED)
        self.btn_delete_inactive = tk.Button(frame_buttons, text=lang["delete_inactive"], command=on_delete_inactive, width=25, state=tk.DISABLED)
        self.btn_copy_table = tk.Button(frame_buttons, text=lang["copy_table"], command=on_copy_table, width=20, state=tk.DISABLED)

        self.btn_start.grid(row=0, column=0, padx=5)
        self.btn_pause.grid(row=0, column=1, padx=5)
        self.btn_confirm.grid(row=0, column=2, padx=5)
        self.btn_copy_inactive.grid(row=0, column=3, padx=5)
        self.btn_delete_inactive.grid(row=0, column=4, padx=5)
        self.btn_copy_table.grid(row=0, column=5, padx=5)

    def refresh_table(self, status_data):
        self.tree.delete(*self.tree.get_children())
        for idx, (tdata_name, row_data) in enumerate(status_data.items(), start=1):
            self.tree.insert("", tk.END, values=(idx, tdata_name, row_data["check"], row_data["live"]))
