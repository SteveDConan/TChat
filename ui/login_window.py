import tkinter as tk
from tkinter import ttk

class LoginWindow:
    def __init__(self, parent, lang):
        self.window = tk.Toplevel(parent)
        self.lang = lang
        self.window.title(self.lang["login_window_title"])
        self.setup_ui()

    def setup_ui(self):
        # Already logged accounts frame
        frame_already = tk.Frame(self.window)
        frame_already.pack(padx=10, pady=5, fill=tk.BOTH, expand=False)

        tk.Label(frame_already, text=self.lang["logged_accounts"], 
                font=("Arial Unicode MS", 10, "bold")).pack(anchor="w")

        self.already_tree = ttk.Treeview(frame_already, columns=("account",), 
                                       show="headings", height=5)
        self.already_tree.heading("account", text=self.lang["logged_accounts"])
        self.already_tree.column("account", width=300)
        self.already_tree.pack(fill=tk.BOTH, expand=True)

        # Telethon button
        self.btn_open_telethon = tk.Button(self.window, text="Open Telethon", 
                                          state=tk.DISABLED, 
                                          font=("Arial Unicode MS", 10, "bold"))
        self.btn_open_telethon.pack(pady=5)

        # Login table
        frame_table = tk.Frame(self.window)
        frame_table.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        columns = ("account", "status")
        self.tree = ttk.Treeview(frame_table, columns=columns, 
                                show="headings", height=10)
        self.tree.heading("account", text="TData")
        self.tree.heading("status", text=self.lang["not_started"])
        self.tree.column("account", width=200, anchor="center")
        self.tree.column("status", width=150, anchor="center")
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Progress frame
        progress_frame = tk.Frame(self.window)
        progress_frame.pack(padx=10, pady=5, fill=tk.X)

        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(progress_frame, 
                                          variable=self.progress_var, 
                                          maximum=100)
        self.progress_bar.pack(fill=tk.X, expand=True)
        self.progress_label = tk.Label(progress_frame, text="0%")
        self.progress_label.pack()

        # Button frame
        frame_buttons = tk.Frame(self.window)
        frame_buttons.pack(pady=5)

        self.btn_create_session = tk.Button(frame_buttons, 
                                          text=self.lang["create_session"],
                                          font=("Arial Unicode MS", 10, "bold"))
        self.btn_update_privacy = tk.Button(frame_buttons, 
                                          text=self.lang["update_privacy"],
                                          font=("Arial Unicode MS", 10, "bold"))
        self.btn_change_info = tk.Button(frame_buttons, 
                                       text=self.lang["change_info"],
                                       font=("Arial Unicode MS", 10, "bold"))

        self.btn_create_session.pack(side=tk.LEFT, padx=5)
        self.btn_update_privacy.pack(side=tk.LEFT, padx=5)
        self.btn_change_info.pack(side=tk.LEFT, padx=5)

        # Delete sessions button
        self.btn_delete_all = tk.Button(self.window, 
                                      text=self.lang["popup_inactive_delete"],
                                      font=("Arial Unicode MS", 10, "bold"))
        self.btn_delete_all.pack(pady=5)

    def update_already_table(self, accounts):
        """Update the table of already logged in accounts"""
        self.already_tree.delete(*self.already_tree.get_children())
        for account in accounts:
            self.already_tree.insert("", tk.END, values=(account,))

    def update_login_status(self, account, status):
        """Update the status of an account in the login table"""
        for item in self.tree.get_children():
            if self.tree.item(item)["values"][0] == account:
                self.tree.item(item, values=(account, status))
                if status == self.lang["processing"]:
                    self.tree.tag_configure("processing", background="yellow")
                    self.tree.item(item, tags=("processing",))
                elif status == self.lang["success"]:
                    self.tree.tag_configure("success", background="lightgreen")
                    self.tree.item(item, tags=("success",))
                elif status == self.lang["failure"]:
                    self.tree.tag_configure("failed", background="tomato")
                    self.tree.item(item, tags=("failed",))
                elif status == self.lang["skipped"]:
                    self.tree.tag_configure("skipped", background="lightblue")
                    self.tree.item(item, tags=("skipped",))
                break

    def update_progress(self, value):
        """Update the progress bar"""
        self.progress_var.set(value)
        self.progress_label.config(text=f"{int(value)}%") 