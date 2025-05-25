import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time


class LoginWindow(tk.Toplevel):
    """
    Popup đăng nhập hàng loạt tài khoản Telegram (multi-account).
    Bao gồm:
    - TreeView danh sách tài khoản đã đăng nhập & chưa đăng nhập.
    - Các nút thao tác: đăng nhập, cập nhật quyền riêng tư, đổi thông tin tài khoản, xóa session.
    - Progress bar hiển thị tiến trình đăng nhập.
    """

    def __init__(
        self,
        master,
        get_tdata_folders_func,
        login_account_func,
        open_telethon_terminal_func,
        update_privacy_func,
        delete_all_sessions_func,
        lang,
        entry_path_value,
        *args,
        **kwargs,
    ):
        super().__init__(master, *args, **kwargs)
        self.title(lang["login_window_title"])
        self.geometry("550x600")
        self.resizable(False, False)

        # Giữ tham chiếu các hàm logic gốc
        self.get_tdata_folders = get_tdata_folders_func
        self.login_account = login_account_func
        self.open_telethon_terminal = open_telethon_terminal_func
        self.update_privacy = update_privacy_func
        self.delete_all_sessions = delete_all_sessions_func
        self.lang = lang
        self.tdata_dir = entry_path_value

        # ===== Giao diện =====
        # --- Tài khoản đã đăng nhập ---
        frame_already = tk.Frame(self)
        frame_already.pack(padx=10, pady=5, fill=tk.BOTH, expand=False)
        tk.Label(
            frame_already,
            text=lang["logged_accounts"],
            font=("Arial Unicode MS", 10, "bold"),
        ).pack(anchor="w")
        self.already_tree = ttk.Treeview(
            frame_already, columns=("account",), show="headings", height=5
        )
        self.already_tree.heading("account", text=lang["logged_accounts"])
        self.already_tree.column("account", width=300)
        self.already_tree.pack(fill=tk.BOTH, expand=True)
        self.update_already_table()

        # --- Mở Telethon session ---
        self.btn_open_telethon = tk.Button(
            self,
            text="Open Telethon",
            state=tk.DISABLED,
            font=("Arial Unicode MS", 10, "bold"),
            command=self.open_telethon_action,
        )
        self.btn_open_telethon.pack(pady=5)
        self.selected_session = {"path": None}
        self.already_tree.bind("<<TreeviewSelect>>", self.on_session_select)

        # --- Danh sách tài khoản chưa đăng nhập ---
        frame_table = tk.Frame(self)
        frame_table.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        columns = ("account", "status")
        self.tree = ttk.Treeview(
            frame_table, columns=columns, show="headings", height=10
        )
        self.tree.heading("account", text="TData")
        self.tree.heading("status", text=lang["not_started"])
        self.tree.column("account", width=200, anchor="center")
        self.tree.column("status", width=150, anchor="center")
        self.tree.pack(fill=tk.BOTH, expand=True)

        # --- Progress Bar ---
        progress_frame = tk.Frame(self)
        progress_frame.pack(padx=10, pady=5, fill=tk.X)
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            progress_frame, variable=self.progress_var, maximum=100
        )
        self.progress_bar.pack(fill=tk.X, expand=True)
        self.progress_label = tk.Label(progress_frame, text="0%")
        self.progress_label.pack()

        # --- Các nút chức năng ---
        frame_buttons_new = tk.Frame(self)
        frame_buttons_new.pack(pady=5)
        self.btn_create_session = tk.Button(
            frame_buttons_new,
            text=lang["create_session"],
            font=("Arial Unicode MS", 10, "bold"),
            command=self.start_login_process,
        )
        self.btn_update_privacy = tk.Button(
            frame_buttons_new,
            text=lang["update_privacy"],
            font=("Arial Unicode MS", 10, "bold"),
            command=self.run_tool,
        )
        self.btn_change_info = tk.Button(
            frame_buttons_new,
            text=lang["change_info"],
            font=("Arial Unicode MS", 10, "bold"),
            command=self.change_account_settings,
        )
        self.btn_create_session.pack(side=tk.LEFT, padx=5)
        self.btn_update_privacy.pack(side=tk.LEFT, padx=5)
        self.btn_change_info.pack(side=tk.LEFT, padx=5)

        # --- Nút xóa session ---
        self.btn_delete_all = tk.Button(
            self,
            text=lang["popup_inactive_delete"],
            font=("Arial Unicode MS", 10, "bold"),
            command=self.delete_all_sessions,
        )
        self.btn_delete_all.pack(pady=5)

        # --- Khởi tạo danh sách tài khoản chưa đăng nhập ---
        self.init_accounts_table()

    # ==== Các method liên quan giao diện ====
    def update_already_table(self):
        """
        Cập nhật bảng tài khoản đã đăng nhập.
        """
        self.already_tree.delete(*self.already_tree.get_children())
        for folder in self.get_tdata_folders(self.tdata_dir):
            session_file = os.path.join(folder, "session.session")
            session_folder = os.path.join(folder, "session")
            if os.path.exists(session_file) or os.path.exists(session_folder):
                self.already_tree.insert("", tk.END, values=(os.path.basename(folder),))

    def on_session_select(self, event):
        """
        Khi chọn 1 session, kích hoạt nút Open Telethon.
        """
        selected = self.already_tree.selection()
        if selected:
            session_name = str(self.already_tree.item(selected[0])["values"][0])
            session_path = os.path.join(self.tdata_dir, session_name)
            self.selected_session["path"] = session_path
            self.btn_open_telethon.config(state=tk.NORMAL)
        else:
            self.btn_open_telethon.config(state=tk.DISABLED)
            self.selected_session["path"] = None

    def open_telethon_action(self):
        """
        Gọi hàm mở Telethon session cho tài khoản đã chọn.
        """
        if self.selected_session["path"]:
            self.open_telethon_terminal(self.selected_session["path"])
        else:
            messagebox.showwarning("Warning", "Chưa chọn session nào.")

    def init_accounts_table(self):
        """
        Lấy danh sách các tdata folder chưa đăng nhập và hiển thị lên treeview.
        """
        all_tdata_folders = self.get_tdata_folders(self.tdata_dir)
        login_tdata_folders = [
            folder
            for folder in all_tdata_folders
            if not (
                os.path.exists(os.path.join(folder, "session.session"))
                or os.path.exists(os.path.join(folder, "session"))
            )
        ]
        self.accounts = [os.path.basename(folder) for folder in login_tdata_folders]
        self.login_tdata_folders = login_tdata_folders
        self.total = len(self.accounts)
        for acc in self.accounts:
            self.tree.insert(
                "", tk.END, iid=acc, values=(acc, self.lang["not_started"])
            )

    # ==== Luồng xử lý đăng nhập ====
    def update_item(self, account, status):
        """
        Cập nhật trạng thái của tài khoản trên treeview.
        """
        self.tree.item(account, values=(account, status))
        if status == self.lang["processing"]:
            self.tree.tag_configure("processing", background="yellow")
            self.tree.item(account, tags=("processing",))
        elif status == self.lang["success"]:
            self.tree.tag_configure("success", background="lightgreen")
            self.tree.item(account, tags=("success",))
        elif status == self.lang["failure"]:
            self.tree.tag_configure("failed", background="tomato")
            self.tree.item(account, tags=("failed",))
        elif status == self.lang["skipped"]:
            self.tree.tag_configure("skipped", background="lightblue")
            self.tree.item(account, tags=("skipped",))
        self.update_idletasks()

    def process_accounts(self):
        """
        Đăng nhập tuần tự các tài khoản, cập nhật trạng thái và progress bar.
        """
        processed = 0
        login_success = []
        login_failure = []
        for idx, folder in enumerate(self.login_tdata_folders):
            acc = os.path.basename(folder)
            # Nếu đã login thì skip
            if os.path.exists(
                os.path.join(folder, "session.session")
            ) or os.path.exists(os.path.join(folder, "session")):
                self.update_item(acc, self.lang["skipped"])
                processed += 1
                percent = (processed / self.total) * 100
                self.progress_var.set(percent)
                self.progress_label.config(text=f"{int(percent)}%")
                continue

            self.update_item(acc, self.lang["processing"])
            result = self.login_account(folder, self.update_item)
            if result:
                login_success.append(acc)
            else:
                login_failure.append(acc)

            processed += 1
            percent = (processed / self.total) * 100
            self.progress_var.set(percent)
            self.progress_label.config(text=f"{int(percent)}%")
            time.sleep(0.5)

        self.update_already_table()

        # Thông báo tổng kết
        summary = (
            f"{self.lang['already_logged']}: {len([a for a in self.accounts if self.tree.item(a)['values'][1]==self.lang['skipped']])}\n"
            f"{self.lang['success']}: {len(login_success)}\n"
            f"{self.lang['failure']}: {len(login_failure)}\n"
        )
        print("Hoàn thành đăng nhập, tổng kết:")
        print(summary)

        messagebox.showinfo("Hoàn thành", self.lang["msg_login_complete"])
        # Nếu muốn, có thể gọi tự động đóng Telegram hoặc các thao tác khác tại đây

    def start_login_process(self):
        """
        Bắt đầu tiến trình đăng nhập hàng loạt.
        """
        self.btn_create_session.config(state=tk.DISABLED)
        threading.Thread(target=self.process_accounts, daemon=True).start()

    # ==== Các nút phụ trợ khác ====
    def run_tool(self):
        """
        Chạy tính năng update privacy cho tất cả tài khoản.
        """
        # Có thể gọi self.update_privacy với từng session path
        messagebox.showinfo(
            "Thông báo", "Chức năng update privacy đang được phát triển."
        )

    def change_account_settings(self):
        """
        Thông báo đổi thông tin tài khoản (future).
        """
        messagebox.showinfo("Thông báo", self.lang["change_info_in_development"])

    def delete_all_sessions(self):
        """
        Xóa tất cả session không hoạt động.
        """
        self.delete_all_sessions_func()
        # Refresh lại danh sách đã login
        self.update_already_table()
        # Nếu muốn, refresh lại danh sách chưa đăng nhập ở tree
