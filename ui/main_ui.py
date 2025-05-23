import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import tkinter.font as tkFont
import threading

from core.config import (
    VERSION_INFO, DEFAULT_TELEGRAM_PATH, CONFIG_FILE,
    CHATGPT_API_KEY, TRANSLATION_ONLY, DEFAULT_TARGET_LANG
)
from core.language import lang
from core.update_utils import check_for_updates
from core.telegram_utils import close_all_telegram, arrange_telegram_windows
from .login_ui import login_all_accounts
from .check_live_ui import warn_check_live
from .settings_ui import open_settings

def init_main_ui():
    """Initialize the main application UI"""
    global root, entry_path, text_stats, text_logged, text_log, telegram_path_entry

    # Create main window
    root = tk.Tk()
    root.title(lang["title"])
    center_window(root, 650, 800)

    # Set default font
    default_font = tkFont.nametofont("TkDefaultFont")
    default_font.configure(family="Arial Unicode MS", size=10)
    root.option_add("*Font", default_font)

    # Start update check in background
    threading.Thread(target=lambda: check_for_updates(root), daemon=True).start()

    # Title
    label_title = tk.Label(root, text=lang["title"], font=("Arial Unicode MS", 14, "bold"))
    label_title.pack(pady=10)

    # Path frame
    frame_path = tk.Frame(root)
    frame_path.pack(pady=5)
    entry_path = tk.Entry(frame_path, width=50)
    entry_path.pack(side=tk.LEFT, padx=5)
    btn_browse = tk.Button(frame_path, text=lang["choose_folder"], command=browse_folder)
    btn_browse.pack(side=tk.LEFT)

    # Telegram path frame
    frame_telegram_path = tk.Frame(root)
    frame_telegram_path.pack(pady=5)
    tk.Label(frame_telegram_path, text=lang["telegram_path_label"]).pack(side=tk.LEFT, padx=5)
    telegram_path_entry = tk.Entry(frame_telegram_path, width=50)
    telegram_path_entry.insert(0, DEFAULT_TELEGRAM_PATH)
    telegram_path_entry.pack(side=tk.LEFT, padx=5)

    # Save path button
    btn_save = tk.Button(root, text=lang["save_path"], command=save_path, width=20)
    btn_save.pack(pady=5)

    # Main buttons frame
    frame_buttons = tk.Frame(root)
    frame_buttons.pack(pady=5)

    def warn_telethon():
        warning_msg = (
            "【Tiếng Việt】: Chức năng Telethon hiện đang trong giai đoạn thử nghiệm. "
            "Vui lòng lưu ý rằng có thể xảy ra một số sự cố hoặc hoạt động không ổn định.\n"
            "【English】: The Telethon feature is currently experimental. "
            "Please note that it may encounter issues or operate unpredictably.\n"
            "【中文】: Telegram 功能目前处于实验阶段，请注意可能存在一些问题或不稳定的情况。"
        )
        messagebox.showwarning("Cảnh báo", warning_msg)
        login_all_accounts(root, entry_path)

    # First row buttons
    btn_login_all = tk.Button(frame_buttons, text=lang["login_all"], command=warn_telethon, width=18)
    btn_copy = tk.Button(frame_buttons, text=lang["copy_telegram"], command=copy_telegram_portable, width=18)
    btn_open = tk.Button(frame_buttons, text=lang["open_telegram"], command=open_telegram_copies, width=18)

    btn_login_all.grid(row=0, column=0, padx=5, pady=5)
    btn_copy.grid(row=0, column=1, padx=5, pady=5)
    btn_open.grid(row=0, column=2, padx=5, pady=5)

    # Second row buttons
    btn_close = tk.Button(frame_buttons, text=lang["close_telegram"],
                         command=lambda: threading.Thread(target=close_all_telegram, daemon=True).start(),
                         width=18)
    btn_arrange = tk.Button(frame_buttons, text=lang["arrange_telegram"],
                          command=lambda: arrange_telegram_windows(arrange_width, arrange_height),
                          width=18)
    btn_auto_it = tk.Button(frame_buttons, text=lang["auto_it"],
                           command=warn_auto_it, width=18)

    btn_close.grid(row=1, column=0, padx=5, pady=5)
    btn_arrange.grid(row=1, column=1, padx=5, pady=5)
    btn_auto_it.grid(row=1, column=2, padx=5, pady=5)

    # Third row buttons
    btn_check_live = tk.Button(frame_buttons, text=lang["check_live"],
                              command=warn_check_live, width=18)
    btn_setting = tk.Button(frame_buttons, text="⚙️ Setting",
                           command=open_settings, width=18)
    btn_update = tk.Button(frame_buttons, text=lang["check_update"],
                          command=lambda: check_for_updates(root), width=18)

    btn_check_live.grid(row=2, column=0, padx=5, pady=5)
    btn_setting.grid(row=2, column=1, padx=5, pady=5)
    btn_update.grid(row=2, column=2, padx=5, pady=5)

    # Stats frame
    frame_stats = tk.Frame(root)
    frame_stats.pack(pady=10)
    label_stats = tk.Label(frame_stats, text=lang["stats_label"])
    label_stats.pack()
    text_stats = tk.Text(frame_stats, width=70, height=10)
    text_stats.pack()

    # Summary frame
    frame_summary = tk.Frame(root)
    frame_summary.pack(pady=10)
    text_summary = tk.Text(frame_summary, width=70, height=5)
    frame_summary.pack_forget()

    # Logged accounts frame
    frame_logged = tk.Frame(root)
    frame_logged.pack(pady=10)
    text_logged = tk.Text(frame_logged, width=70, height=5)
    frame_logged.pack_forget()

    # Log frame
    frame_log = tk.Frame(root)
    frame_log.pack(pady=10)
    label_log = tk.Label(frame_log, text=lang["log_label"])
    label_log.pack()
    text_log = tk.Text(frame_log, width=70, height=10)
    text_log.pack()

    # Load saved path
    saved_path = load_path()
    if saved_path:
        entry_path.insert(0, saved_path)
        update_stats()
        update_logged()

    # Footer
    footer = tk.Label(root, text=VERSION_INFO, font=("Arial Unicode MS", 8))
    footer.pack(side="bottom", fill="x", pady=5)

    # Set window close handler
    root.protocol("WM_DELETE_WINDOW", on_closing)

    # Initialize mini chat
    from mini_chat import set_root, set_mini_chat_globals, create_mini_chat, create_mini_chatgpt, start_mini_chat_monitor
    set_root(root)
    set_mini_chat_globals(CHATGPT_API_KEY, TRANSLATION_ONLY, DEFAULT_TARGET_LANG)
    create_mini_chat()
    create_mini_chatgpt()
    start_mini_chat_monitor()

    print("Consolog: Giao diện chính được khởi tạo thành công.")
    root.mainloop()

def center_window(win, width, height):
    """Center a window on screen"""
    win.update_idletasks()
    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    win.geometry(f"{width}x{height}+{x}+{y}")

def browse_folder():
    """Open folder browser dialog"""
    folder_selected = filedialog.askdirectory()
    print(f"Consolog: Người dùng chọn folder: {folder_selected}")
    entry_path.delete(0, tk.END)
    entry_path.insert(0, folder_selected)

def save_path():
    """Save the current path to config file"""
    folder_path = entry_path.get()
    print(f"Consolog: Lưu đường dẫn: {folder_path}")
    if os.path.exists(folder_path):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write(folder_path)
        messagebox.showinfo("Lưu thành công", lang["msg_saved_path"])
        update_stats()
        update_logged()
    else:
        messagebox.showerror("Lỗi", lang["msg_error_path"])

def load_path():
    """Load path from config file"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            path = f.read().strip()
            print(f"Consolog: Đường dẫn tải được: {path}")
            return path
    return ""

def update_stats():
    """Update statistics display"""
    folder_path = entry_path.get()
    if not os.path.exists(folder_path):
        return
    try:
        subfolders = [d for d in os.listdir(folder_path)
                     if os.path.isdir(os.path.join(folder_path, d))]
    except Exception as e:
        messagebox.showerror("Lỗi", f"Không thể đọc thư mục: {e}")
        return

    info_list = []
    for sub in subfolders:
        sub_path = os.path.join(folder_path, sub)
        tdata_count = sum(
            1 for item in os.listdir(sub_path)
            if item.lower() == 'tdata' and os.path.isdir(os.path.join(sub_path, item))
        )
        info_list.append(f"- {sub}: có {tdata_count} tdata folder(s)")

    info_text = "\n".join(info_list) if info_list else "Không có thư mục con nào."
    text_stats.delete("1.0", tk.END)
    text_stats.insert(tk.END, info_text)
    print("Consolog: Cập nhật stats thành công.")

def update_logged():
    """Update logged accounts display"""
    tdata_dir = entry_path.get()
    logged_list = []
    for folder in get_tdata_folders(tdata_dir):
        session_file = os.path.join(folder, "session.session")
        session_folder = os.path.join(folder, "session")
        if os.path.exists(session_file) or os.path.exists(session_folder):
            logged_list.append(os.path.basename(folder))

    text_logged.delete("1.0", tk.END)
    if logged_list:
        text_logged.insert(tk.END, ", ".join(logged_list))
    else:
        text_logged.insert(tk.END, lang["not_found"])
    print("Consolog: Cập nhật logged sessions.")

def get_tdata_folders(main_dir):
    """Get list of TData folders"""
    if not os.path.exists(main_dir):
        return []
    folders = [
        os.path.join(main_dir, f) for f in os.listdir(main_dir)
        if os.path.isdir(os.path.join(main_dir, f))
    ]
    print(f"Consolog: Tìm thấy {len(folders)} thư mục TData trong {main_dir}")
    return folders

def on_closing():
    """Handle application closing"""
    print("Consolog: Kiểm tra và xóa session chưa hoàn thành trước khi tắt tool...")
    tdata_dir = entry_path.get()
    if os.path.exists(tdata_dir):
        folders = get_tdata_folders(tdata_dir)
        for folder in folders:
            phone = os.path.basename(folder)
            if phone not in successful_sessions:
                print(f"Consolog: Xóa session chưa hoàn thành cho {phone}")
                cleanup_session_files(os.path.join(folder, "session"))
                session_file = os.path.join(folder, "session.session")
                if os.path.exists(session_file):
                    try:
                        os.remove(session_file)
                        print(f"Consolog: Đã xóa file session {session_file}")
                    except Exception as e:
                        print(f"Consolog [ERROR]: Lỗi xóa file session {session_file}: {e}")
    root.destroy()

def warn_auto_it():
    """Show warning before launching AutoIT feature"""
    try:
        from mini_chat import destroy_mini_chat
        destroy_mini_chat()
        print("Consolog: Mini chat đã được đóng khi bật chức năng AutoIT.")
    except Exception as e:
        print("Consolog [WARNING]: Không thể đóng mini chat:", e)

    warning_msg = (
        "【Tiếng Việt】: Trước khi khởi chạy chức năng AutoIT, chúng tôi khuyến nghị bạn kiểm tra "
        "trạng thái trực tiếp của các tài khoản Telegram. Điều này sẽ đảm bảo tất cả các tài khoản "
        "đều hoạt động bình thường, từ đó tối ưu hóa hiệu suất của quá trình tự động.\n"
        "【English】: Before initiating the AutoIT function, we strongly recommend performing a live "
        "check on your Telegram accounts. This will ensure that all accounts are active and optimize "
        "the automation process.\n"
        "【中文】: 在启动 AutoIT 功能之前，我们强烈建议您先对所有 Telegram 账户进行实时检查，"
        "确保它们均处于活跃状态，从而优化自动化过程的效率。"
    )
    messagebox.showinfo("Khuyến cáo", warning_msg)
    from autoit_module import auto_it_function
    auto_it_function(root, entry_path, lang, get_tdata_folders) 