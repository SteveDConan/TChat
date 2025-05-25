# ui/login_window.py

import tkinter as tk
from tkinter import ttk, messagebox
import threading

def create_login_window(
    root,
    lang,
    get_tdata_folders,
    entry_path,
    login_account_callback,
    open_telethon_callback,
    delete_all_sessions_callback,
    update_privacy_callback,
    change_account_settings_callback
):
    """
    Hàm tạo giao diện cửa sổ đăng nhập nhiều account.

    Tham số:
        - root: Tk hoặc Toplevel cha
        - lang: dict ngôn ngữ
        - get_tdata_folders: hàm trả về list folder tdata
        - entry_path: Entry chứa đường dẫn tdata
        - login_account_callback: hàm xử lý login từng account
        - open_telethon_callback: hàm mở terminal Telethon
        - delete_all_sessions_callback: hàm xóa session chưa login
        - update_privacy_callback: hàm cập nhật quyền riêng tư
        - change_account_settings_callback: hàm đổi thông tin tài khoản
    """

    login_window = tk.Toplevel(root)
    login_window.title(lang["login_window_title"])
    login_window.geometry("550x600")

    # --- Các account đã đăng nhập ---
    frame_already = tk.Frame(login_window)
    frame_already.pack(padx=10, pady=5, fill=tk.BOTH, expand=False)

    tk.Label(frame_already, text=lang["logged_accounts"], font=("Arial Unicode MS", 10, "bold")).pack(anchor="w")
    already_tree = ttk.Treeview(frame_already, columns=("account",), show="headings", height=5)
    already_tree.heading("account", text=lang["logged_accounts"])
    already_tree.column("account", width=300)
    already_tree.pack(fill=tk.BOTH, expand=True)

    # Cập nhật bảng account đã login
    def update_already_table():
        already_tree.delete(*already_tree.get_children())
        tdata_dir = entry_path.get()
        for folder in get_tdata_folders(tdata_dir):
            session_file = os.path.join(folder, "session.session")
            session_folder = os.path.join(folder, "session")
            if os.path.exists(session_file) or os.path.exists(session_folder):
                already_tree.insert("", tk.END, values=(os.path.basename(folder),))

    update_already_table()

    # --- Nút mở Telethon terminal ---
    btn_open_telethon = tk.Button(login_window, text="Open Telethon", state=tk.DISABLED, font=("Arial Unicode MS", 10, "bold"))
    btn_open_telethon.pack(pady=5)

    selected_session = {"path": None}

    def on_session_select(event):
        selected = already_tree.selection()
        if selected:
            session_name = str(already_tree.item(selected[0])["values"][0])
            tdata_dir = entry_path.get()
            session_path = os.path.join(tdata_dir, session_name)
            selected_session["path"] = session_path
            btn_open_telethon.config(state=tk.NORMAL)
        else:
            btn_open_telethon.config(state=tk.DISABLED)
            selected_session["path"] = None

    already_tree.bind("<<TreeviewSelect>>", on_session_select)

    def open_telethon_action():
        if selected_session["path"]:
            open_telethon_callback(selected_session["path"])
        else:
            messagebox.showwarning("Warning", "Chưa chọn session nào.")

    btn_open_telethon.config(command=open_telethon_action)

    # --- Account cần login ---
    tdata_dir = entry_path.get()
    all_tdata_folders = get_tdata_folders(tdata_dir)
    login_tdata_folders = [
        folder for folder in all_tdata_folders
        if not (os.path.exists(os.path.join(folder, "session.session")) or os.path.exists(os.path.join(folder, "session")))
    ]
    accounts = [os.path.basename(folder) for folder in login_tdata_folders]
    total = len(accounts)

    frame_table = tk.Frame(login_window)
    frame_table.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

    columns = ("account", "status")
    tree = ttk.Treeview(frame_table, columns=columns, show="headings", height=10)
    tree.heading("account", text="TData")
    tree.heading("status", text=lang["not_started"])
    tree.column("account", width=200, anchor="center")
    tree.column("status", width=150, anchor="center")
    tree.pack(fill=tk.BOTH, expand=True)

    for acc in accounts:
        tree.insert("", tk.END, iid=acc, values=(acc, lang["not_started"]))

    # --- Progress bar ---
    progress_frame = tk.Frame(login_window)
    progress_frame.pack(padx=10, pady=5, fill=tk.X)
    progress_var = tk.DoubleVar(value=0)
    progress_bar = ttk.Progressbar(progress_frame, variable=progress_var, maximum=100)
    progress_bar.pack(fill=tk.X, expand=True)
    progress_label = tk.Label(progress_frame, text="0%")
    progress_label.pack()

    # --- Nút thao tác ---
    frame_buttons_new = tk.Frame(login_window)
    frame_buttons_new.pack(pady=5)
    btn_create_session = tk.Button(frame_buttons_new, text=lang["create_session"], font=("Arial Unicode MS", 10, "bold"))
    btn_update_privacy = tk.Button(frame_buttons_new, text=lang["update_privacy"], font=("Arial Unicode MS", 10, "bold"), command=update_privacy_callback)
    btn_change_info = tk.Button(frame_buttons_new, text=lang["change_info"], font=("Arial Unicode MS", 10, "bold"), command=change_account_settings_callback)
    btn_create_session.pack(side=tk.LEFT, padx=5)
    btn_update_privacy.pack(side=tk.LEFT, padx=5)
    btn_change_info.pack(side=tk.LEFT, padx=5)

    btn_delete_all = tk.Button(login_window, text=lang["popup_inactive_delete"], font=("Arial Unicode MS", 10, "bold"), command=delete_all_sessions_callback)
    btn_delete_all.pack(pady=5)

    # --- Helper update status ---
    def update_item(account, status):
        tree.item(account, values=(account, status))
        if status == lang["processing"]:
            tree.tag_configure("processing", background="yellow")
            tree.item(account, tags=("processing",))
        elif status == lang["success"]:
            tree.tag_configure("success", background="lightgreen")
            tree.item(account, tags=("success",))
        elif status == lang["failure"]:
            tree.tag_configure("failed", background="tomato")
            tree.item(account, tags=("failed",))
        elif status == lang["skipped"]:
            tree.tag_configure("skipped", background="lightblue")
            tree.item(account, tags=("skipped",))
        login_window.update_idletasks()

    # --- Xử lý đăng nhập tất cả ---
    def process_accounts():
        processed = 0
        login_success = []
        login_failure = []
        for folder in login_tdata_folders:
            acc = os.path.basename(folder)
            if os.path.exists(os.path.join(folder, "session.session")) or os.path.exists(os.path.join(folder, "session")):
                update_item(acc, lang["skipped"])
                processed += 1
                percent = (processed / total) * 100
                login_window.after(0, progress_var.set, percent)
                login_window.after(0, progress_label.config, {"text": f"{int(percent)}%"})
                continue

            login_window.after(0, update_item, acc, lang["processing"])
            result = login_account_callback(folder, update_item)
            if result:
                login_success.append(acc)
            else:
                login_failure.append(acc)

            processed += 1
            percent = (processed / total) * 100
            login_window.after(0, progress_var.set, percent)
            login_window.after(0, progress_label.config, {"text": f"{int(percent)}%"})
            # Có thể sleep nhẹ ở đây nếu muốn, ví dụ: time.sleep(0.5)

        login_window.after(0, update_already_table)
        summary = (
            f"{lang['already_logged']}: {len([a for a in accounts if tree.item(a)['values'][1]==lang['skipped']])}\n"
            f"{lang['success']}: {len(login_success)}\n"
            f"{lang['failure']}: {len(login_failure)}\n"
        )
        login_window.after(0, messagebox.showinfo, "Hoàn thành", lang["msg_login_complete"])

    def start_login_process():
        btn_create_session.config(state=tk.DISABLED)
        threading.Thread(target=process_accounts, daemon=True).start()

    btn_create_session.config(command=start_login_process)

    # Hoàn tất setup
    return login_window
