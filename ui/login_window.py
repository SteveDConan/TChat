import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time

class LoginWindow(tk.Toplevel):
    """
    Cửa sổ đăng nhập nhiều tài khoản Telegram (multi-account).
    Có hiển thị các tài khoản đã đăng nhập, cần đăng nhập, và trạng thái từng tài khoản.
    """
    def __init__(self, master, lang, tdata_folders, login_account_func, open_telethon_func, delete_all_sessions_func, change_account_settings_func):
        super().__init__(master)
        self.title(lang["login_window_title"])
        self.lang = lang
        self.tdata_folders = tdata_folders
        self.login_account_func = login_account_func
        self.open_telethon_func = open_telethon_func
        self.delete_all_sessions_func = delete_all_sessions_func
        self.change_account_settings_func = change_account_settings_func

        self.geometry("550x600")
        self.resizable(False, False)

        # Frame hiển thị các tài khoản đã đăng nhập
        frame_already = tk.Frame(self)
        frame_already.pack(padx=10, pady=5, fill=tk.BOTH, expand=False)

        tk.Label(frame_already, text=lang["logged_accounts"], font=("Arial Unicode MS", 10, "bold")).pack(anchor="w")
        self.already_tree = ttk.Treeview(frame_already, columns=("account",), show="headings", height=5)
        self.already_tree.heading("account", text=lang["logged_accounts"])
        self.already_tree.column("account", width=300)
        self.already_tree.pack(fill=tk.BOTH, expand=True)

        # Frame các tài khoản cần đăng nhập
        frame_table = tk.Frame(self)
        frame_table.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        columns = ("account", "status")
        self.tree = ttk.Treeview(frame_table, columns=columns, show="headings", height=10)
        self.tree.heading("account", text="TData")
        self.tree.heading("status", text=lang["not_started"])
        self.tree.column("account", width=200, anchor="center")
        self.tree.column("status", width=150, anchor="center")
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Progress bar & label
        progress_frame = tk.Frame(self)
        progress_frame.pack(padx=10, pady=5, fill=tk.X)

        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, expand=True)
        self.progress_label = tk.Label(progress_frame, text="0%")
        self.progress_label.pack()

        # Nút chức năng
        frame_buttons_new = tk.Frame(self)
        frame_buttons_new.pack(pady=5)
        self.btn_create_session = tk.Button(frame_buttons_new, text=lang["create_session"], font=("Arial Unicode MS", 10, "bold"), command=self.start_login_process)
        btn_update_privacy = tk.Button(frame_buttons_new, text=lang["update_privacy"], font=("Arial Unicode MS", 10, "bold"))
        btn_change_info = tk.Button(frame_buttons_new, text=lang["change_info"], font=("Arial Unicode MS", 10, "bold"), command=self.change_account_settings_func)
        self.btn_create_session.pack(side=tk.LEFT, padx=5)
        btn_update_privacy.pack(side=tk.LEFT, padx=5)
        btn_change_info.pack(side=tk.LEFT, padx=5)

        self.btn_delete_all = tk.Button(self, text=lang["popup_inactive_delete"], font=("Arial Unicode MS", 10, "bold"), command=self.delete_all_sessions_func)
        self.btn_delete_all.pack(pady=5)

        # Nút open telethon
        self.btn_open_telethon = tk.Button(self, text="Open Telethon", state=tk.DISABLED, font=("Arial Unicode MS", 10, "bold"), command=self.open_telethon_action)
        self.btn_open_telethon.pack(pady=5)

        # Sự kiện chọn trên bảng tài khoản đã đăng nhập
        self.selected_session = {"path": None}
        self.already_tree.bind("<<TreeviewSelect>>", self.on_session_select)

        self.update_already_table()
        self.populate_tree()

    def update_already_table(self):
        """Cập nhật bảng tài khoản đã đăng nhập"""
        self.already_tree.delete(*self.already_tree.get_children())
        for folder in self.tdata_folders:
            session_file = f"{folder}/session.session"
            session_folder = f"{folder}/session"
            # Giả sử check file ở đây (bạn sẽ truyền hàm check từ ngoài vào tốt hơn)
            import os
            if os.path.exists(session_file) or os.path.exists(session_folder):
                self.already_tree.insert("", tk.END, values=(os.path.basename(folder),))

    def populate_tree(self):
        """Cập nhật bảng tài khoản cần đăng nhập"""
        for folder in self.tdata_folders:
            acc = os.path.basename(folder)
            self.tree.insert("", tk.END, iid=acc, values=(acc, self.lang["not_started"]))

    def on_session_select(self, event):
        selected = self.already_tree.selection()
        if selected:
            session_name = str(self.already_tree.item(selected[0])["values"][0])
            self.selected_session["path"] = session_name  # có thể sửa lại path cho đúng
            self.btn_open_telethon.config(state=tk.NORMAL)
        else:
            self.btn_open_telethon.config(state=tk.DISABLED)
            self.selected_session["path"] = None

    def open_telethon_action(self):
        if self.selected_session["path"]:
            self.open_telethon_func(self.selected_session["path"])
        else:
            messagebox.showwarning("Warning", "Chưa chọn session nào.")

    def start_login_process(self):
        self.btn_create_session.config(state=tk.DISABLED)
        threading.Thread(target=self.process_accounts, daemon=True).start()

    def process_accounts(self):
        total = len(self.tdata_folders)
        processed = 0
        for folder in self.tdata_folders:
            acc = os.path.basename(folder)
            # Giả lập quá trình login
            self.tree.item(acc, values=(acc, self.lang["processing"]))
            time.sleep(0.5)  # Bạn sẽ gọi login_account_func(folder, ...)
            self.tree.item(acc, values=(acc, self.lang["success"]))
            processed += 1
            percent = (processed / total) * 100
            self.progress_var.set(percent)
            self.progress_label.config(text=f"{int(percent)}%")
            self.update_idletasks()
        messagebox.showinfo("Hoàn thành", self.lang["msg_login_complete"])
