import os
import time
import shutil
import subprocess
import asyncio
import math
import ctypes
from ctypes import wintypes
import threading
import re
import random

import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from tkinter import ttk
import tkinter.font as tkFont
from PIL import Image, ImageChops, ImageTk
import requests
from packaging.version import Version

try:
    from send2trash import send2trash
except ImportError:
    send2trash = None

try:
    import psutil
except ImportError:
    psutil = None

from telethon.sync import TelegramClient
from telethon import functions, types, events
from telethon.errors import (
    SessionPasswordNeededError,
    PhoneCodeInvalidError,
    PhoneCodeExpiredError,
)

from resources.languages import languages
from resources.config import (
    API_ID,
    API_HASH,
    CURRENT_VERSION,
    GITHUB_USER,
    GITHUB_REPO,
    CONFIG_FILE,
    WINDOW_SIZE_FILE,
    CHATGPT_API_KEY_FILE,
    DEFAULT_TELEGRAM_PATH,
    DEFAULT_TARGET_LANG,
    TRANSLATION_ONLY,
    VERSION_INFO,
)
from resources.utils import (
    center_window,
    copy_to_clipboard,
    get_tdata_folders,
    log_message,
    load_window_size,
    save_window_size,
    load_chatgpt_api_key,
    save_chatgpt_api_key,
    read_file,
    write_file,
)
from cores.session import (
    check_authorization,
    cleanup_session_files,
    parse_2fa_info,
    get_otp,
    async_login,
    login_account,
)
from cores.manager import (
    get_tdata_folders,
    copy_telegram_portable,
    cleanup_all_sessions,
    count_valid_tdata,
    status_report,
    check_folder_exists,
    check_file_exists,
)
from cores.privacy import update_privacy_sync, run_update_privacy_multi

CHATGPT_API_KEY = load_chatgpt_api_key(CHATGPT_API_KEY_FILE)

arrange_width = 500
arrange_height = 504

user32 = ctypes.windll.user32

lang = {}
successful_sessions = set()

if not psutil:
    print("[CẢNH BÁO] psutil chưa được cài đặt, một số chức năng sẽ không hoạt động!")


def get_window_handle_by_pid(pid):
    """Tìm HWND của cửa sổ dựa vào PID."""
    handles = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
    def enum_callback(hwnd, lParam):
        if user32.IsWindow(hwnd) and user32.IsWindowVisible(hwnd):
            window_pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(window_pid))
            if window_pid.value == pid:
                handles.append(hwnd)
        return True

    user32.EnumWindows(enum_callback, 0)
    return handles[0] if handles else None


def close_all_telegram_threaded():
    threading.Thread(target=close_all_telegram, daemon=True).start()


def auto_close_telegram():
    """Tự động đóng tất cả tiến trình Telegram."""
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq Telegram.exe", "/FO", "CSV"],
            capture_output=True,
            text=True,
        )
        output = result.stdout.strip().splitlines()
        pids = []
        for line in output[1:]:
            parts = line.replace('"', "").split(",")
            if len(parts) >= 2:
                pid = parts[1].strip()
                pids.append(pid)
        for pid in pids:
            subprocess.run(
                ["taskkill", "/F", "/PID", pid], capture_output=True, text=True
            )
            time.sleep(1)
        while True:
            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq Telegram.exe", "/FO", "CSV"],
                capture_output=True,
                text=True,
            )
            lines = result.stdout.strip().splitlines()
            if len(lines) <= 1:
                break
            time.sleep(1)
        return True
    except Exception as e:
        print(f"Lỗi khi tự động tắt Telegram: {e}")
        return False


def close_all_telegram():
    """Đóng tất cả tiến trình Telegram.exe đang chạy trên hệ thống."""
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq Telegram.exe", "/FO", "CSV"],
            capture_output=True,
            text=True,
        )
        output = result.stdout.strip().splitlines()
        pids = []
        for line in output[1:]:
            parts = line.replace('"', "").split(",")
            if len(parts) >= 2:
                pids.append(parts[1])
        closed = []
        errors = []
        for pid in pids:
            try:
                subprocess.run(
                    ["taskkill", "/F", "/PID", pid], capture_output=True, text=True
                )
                closed.append(pid)
                time.sleep(1)
            except Exception as e:
                errors.append(f"PID {pid}: {e}")
        summary = lang.get("close_result", "").format(
            closed=", ".join(closed) if closed else "None",
            errors="; ".join(errors) if errors else "None",
        )
        log_message(summary)
        messagebox.showinfo(lang.get("close_result_title", "Kết quả"), summary)
    except Exception as e:
        messagebox.showerror("Lỗi", f"Không thể đóng các tiến trình Telegram: {e}")


# ======== HẾT PHẦN 1/6 ========
def delete_all_sessions():
    """Xóa tất cả file session trong thư mục đã chọn."""
    tdata_dir = ""
    try:
        tdata_dir = entry_path.get()
    except Exception:
        pass
    if not os.path.exists(tdata_dir):
        messagebox.showerror(
            "Lỗi", lang.get("msg_error_path", "Không tìm thấy thư mục!")
        )
        return
    tdata_folders = get_tdata_folders(tdata_dir)
    deleted_accounts = []
    for folder in tdata_folders:
        session_folder = os.path.join(folder, "session")
        session_file = os.path.join(folder, "session.session")
        if os.path.exists(session_file):
            try:
                os.remove(session_file)
            except Exception:
                pass
        if os.path.exists(session_folder) and os.path.isdir(session_folder):
            try:
                shutil.rmtree(session_folder)
            except Exception:
                pass
        deleted_accounts.append(os.path.basename(folder))
    messagebox.showinfo(
        lang.get("popup_inactive_title", "Thông báo"),
        "Đã xóa session của các tài khoản: " + ", ".join(deleted_accounts),
    )


def save_path():
    """Lưu đường dẫn được chọn vào file cấu hình (dùng cho thao tác tdata)."""
    folder_path = entry_path.get()
    if os.path.exists(folder_path):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write(folder_path)
        messagebox.showinfo(
            "Lưu thành công", lang.get("msg_saved_path", "Đã lưu đường dẫn!")
        )
    else:
        messagebox.showerror(
            "Lỗi", lang.get("msg_error_path", "Thư mục không tồn tại!")
        )


def load_path():
    """Đọc đường dẫn từ file cấu hình."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                path = f.read().strip()
                return path
        except UnicodeDecodeError:
            try:
                with open(CONFIG_FILE, "r", encoding="latin-1") as f:
                    path = f.read().strip()
                    return path
            except Exception as e:
                print(f"Lỗi đọc file cấu hình: {e}")
                return ""
        except Exception as e:
            print(f"Lỗi đọc file cấu hình: {e}")
            return ""
    return ""


def browse_folder():
    """Hiện hộp thoại chọn thư mục cho user."""
    folder_selected = filedialog.askdirectory()
    entry_path.delete(0, tk.END)
    entry_path.insert(0, folder_selected)


# ======== HẾT PHẦN 2/6 ========
def open_telegram_with_tdata(tdata_folder):
    """Mở Telegram với tdata folder được chỉ định."""
    telegram_exe = os.path.join(tdata_folder, "telegram.exe")
    tdata_sub = os.path.join(tdata_folder, "tdata")
    if not os.path.exists(telegram_exe):
        log_message(f"Không tìm thấy telegram.exe tại {telegram_exe}")
        return None
    if not os.path.exists(tdata_sub):
        log_message(f"Không tìm thấy thư mục tdata tại {tdata_sub}")
        return None
    log_message(f"Đang mở {telegram_exe} (cwd={tdata_folder})")
    proc = subprocess.Popen([telegram_exe], cwd=tdata_folder)
    time.sleep(1)
    return proc


def change_account_settings():
    messagebox.showinfo(
        "Thông báo",
        lang.get("change_info_in_development", "Chức năng đang phát triển!"),
    )


def update_privacy(session_path):
    """Ẩn số điện thoại & cuộc gọi cho 1 session Telegram."""

    async def run_update():
        client = TelegramClient(session_path, API_ID, API_HASH)
        try:
            await client.connect()
        except Exception as e:
            log_message(f"Lỗi kết nối cho {session_path}: {e}")
            return
        try:
            await client(
                functions.account.SetPrivacyRequest(
                    key=types.InputPrivacyKeyPhoneNumber(),
                    rules=[types.InputPrivacyValueDisallowAll()],
                )
            )
            if hasattr(types, "InputPrivacyKeyCalls"):
                await client(
                    functions.account.SetPrivacyRequest(
                        key=types.InputPrivacyKeyCalls(),
                        rules=[types.InputPrivacyValueDisallowAll()],
                    )
                )
            log_message(
                f"Cập nhật quyền riêng tư thành công cho session {session_path}"
            )
        except Exception as e:
            log_message(f"Lỗi cập nhật quyền riêng tư cho session {session_path}: {e}")
        await client.disconnect()

    asyncio.run(run_update())


def run_tool():
    """Batch cập nhật quyền riêng tư cho toàn bộ tài khoản."""
    tdata_dir = entry_path.get()
    if not os.path.exists(tdata_dir):
        messagebox.showerror(
            "Lỗi", lang.get("msg_error_path", "Không tìm thấy thư mục!")
        )
        return
    tdata_folders = get_tdata_folders(tdata_dir)
    for folder in tdata_folders:
        open_telegram_with_tdata(folder)
    time.sleep(10)
    for folder in tdata_folders:
        session_path = os.path.join(folder, "session")
        try:
            asyncio.run(update_privacy(session_path))
        except Exception as e:
            log_message(f"Lỗi cập nhật quyền riêng tư cho {folder}: {e}")
    messagebox.showinfo(
        "Hoàn thành", lang.get("msg_privacy_complete", "Đã cập nhật quyền riêng tư!")
    )
    log_message("Đã hoàn tất cập nhật quyền riêng tư.")


def open_settings():
    """Cửa sổ tùy chỉnh: kích thước Telegram, ChatGPT key, ngôn ngữ dịch."""
    popup = tk.Toplevel(root)
    popup.title("Setting - Tùy chỉnh sắp xếp & ChatGPT")
    center_window(popup, 400, 350)
    lbl_info = tk.Label(
        popup,
        text="Nhập kích thước cửa sổ sắp xếp:\nx = (số cột) × Custom Width, y = (số hàng) × Custom Height",
        wraplength=380,
    )
    lbl_info.pack(pady=10)
    frame_entries = tk.Frame(popup)
    frame_entries.pack(pady=5)
    tk.Label(frame_entries, text="Custom Width:").grid(
        row=0, column=0, padx=5, pady=5, sticky="e"
    )
    entry_width = tk.Entry(frame_entries, width=10)
    entry_width.insert(0, str(arrange_width))
    entry_width.grid(row=0, column=1, padx=5, pady=5)
    tk.Label(frame_entries, text="Custom Height:").grid(
        row=1, column=0, padx=5, pady=5, sticky="e"
    )
    entry_height = tk.Entry(frame_entries, width=10)
    entry_height.insert(0, str(arrange_height))
    entry_height.grid(row=1, column=1, padx=5, pady=5)
    tk.Label(popup, text="ChatGPT API Key:").pack(pady=5)
    chatgpt_key_entry = tk.Entry(popup, width=50)
    chatgpt_key_entry.insert(0, load_chatgpt_api_key(CHATGPT_API_KEY_FILE))
    chatgpt_key_entry.pack(pady=5)
    tk.Label(popup, text="Default Translation Language (Target):").pack(pady=5)
    translation_lang_var = tk.StringVar(value=DEFAULT_TARGET_LANG)
    translation_lang_menu = tk.OptionMenu(popup, translation_lang_var, "vi", "en", "zh")
    translation_lang_menu.pack(pady=5)

    def save_settings():
        global arrange_width, arrange_height, CHATGPT_API_KEY, DEFAULT_TARGET_LANG
        try:
            w = int(entry_width.get())
            h = int(entry_height.get())
            arrange_width = w
            arrange_height = h
            save_chatgpt_api_key(chatgpt_key_entry.get().strip())
            CHATGPT_API_KEY = chatgpt_key_entry.get().strip()
            DEFAULT_TARGET_LANG = translation_lang_var.get()
            messagebox.showinfo(
                "Setting",
                "Đã lưu cấu hình sắp xếp, ChatGPT API Key và ngôn ngữ dịch mặc định!",
            )
            popup.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Giá trị không hợp lệ: {e}")

    btn_save = tk.Button(popup, text="Save", command=save_settings)
    btn_save.pack(pady=10)
    popup.transient(root)
    popup.grab_set()
    root.wait_window(popup)


def select_language():
    """Chọn ngôn ngữ giao diện ban đầu."""
    lang_window = tk.Tk()
    lang_window.title(languages["en"]["lang_select_title"])
    center_window(lang_window, 400, 200)
    tk.Label(
        lang_window,
        text="Select Language / 选择语言 / Chọn ngôn ngữ:",
        font=("Arial Unicode MS", 12),
    ).pack(pady=10)
    language_var = tk.StringVar(value="en")
    for code in ["vi", "en", "zh"]:
        tk.Radiobutton(
            lang_window,
            text=languages[code]["lang_" + code],
            variable=language_var,
            value=code,
            font=("Arial Unicode MS", 10),
        ).pack(anchor="w", padx=20)
    tk.Label(lang_window, text=VERSION_INFO, font=("Arial Unicode MS", 8)).pack(pady=5)
    tk.Button(
        lang_window,
        text="OK",
        command=lambda: set_language(language_var, lang_window),
        font=("Arial Unicode MS", 10),
    ).pack(pady=10)
    lang_window.mainloop()


def set_language(language_var, window):
    global lang
    selected = language_var.get()
    lang = languages[selected]
    window.destroy()
    init_main_ui()


def show_splash_screen():
    splash = tk.Tk()
    splash.overrideredirect(True)
    width, height = 300, 150
    screen_width = splash.winfo_screenwidth()
    screen_height = splash.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    splash.geometry(f"{width}x{height}+{x}+{y}")
    label = tk.Label(
        splash, text="Loading, please wait...", font=("Arial Unicode MS", 12)
    )
    label.pack(expand=True)
    threading.Thread(target=lambda: load_tool(splash), daemon=True).start()
    splash.mainloop()


def load_tool(splash):
    time.sleep(2)
    splash.after(0, lambda: finish_splash(splash))


def finish_splash(splash):
    splash.destroy()
    select_language()


def on_closing():
    tdata_dir = entry_path.get()
    if os.path.exists(tdata_dir):
        folders = get_tdata_folders(tdata_dir)
        for folder in folders:
            phone = os.path.basename(folder)
            if phone not in successful_sessions:
                cleanup_session_files(os.path.join(folder, "session"))
                session_file = os.path.join(folder, "session.session")
                if os.path.exists(session_file):
                    try:
                        os.remove(session_file)
                    except Exception:
                        pass
    root.destroy()


def init_main_ui():
    """Giao diện chính của ứng dụng."""
    global root, entry_path, text_stats, text_logged, text_summary, text_log, telegram_path_entry
    root = tk.Tk()
    root.title(lang["title"])
    center_window(root, 650, 800)
    default_font = tkFont.nametofont("TkDefaultFont")
    default_font.configure(family="Arial Unicode MS", size=10)
    root.option_add("*Font", default_font)
    label_title = tk.Label(
        root, text=lang["title"], font=("Arial Unicode MS", 14, "bold")
    )
    label_title.pack(pady=10)
    frame_path = tk.Frame(root)
    frame_path.pack(pady=5)
    entry_path = tk.Entry(frame_path, width=50)
    entry_path.pack(side=tk.LEFT, padx=5)
    btn_browse = tk.Button(
        frame_path, text=lang["choose_folder"], command=browse_folder
    )
    btn_browse.pack(side=tk.LEFT)
    frame_telegram_path = tk.Frame(root)
    frame_telegram_path.pack(pady=5)
    tk.Label(frame_telegram_path, text=lang["telegram_path_label"]).pack(
        side=tk.LEFT, padx=5
    )
    telegram_path_entry = tk.Entry(frame_telegram_path, width=50)
    telegram_path_entry.insert(0, DEFAULT_TELEGRAM_PATH)
    telegram_path_entry.pack(side=tk.LEFT, padx=5)
    btn_save = tk.Button(root, text=lang["save_path"], command=save_path, width=20)
    btn_save.pack(pady=5)
    frame_buttons = tk.Frame(root)
    frame_buttons.pack(pady=5)

    btn_copy = tk.Button(
        frame_buttons,
        text=lang["copy_telegram"],
        command=lambda: copy_telegram_portable(),
        width=18,
    )
    btn_open = tk.Button(
        frame_buttons,
        text=lang["open_telegram"],
        command=lambda: open_telegram_copies(),
        width=18,
    )
    btn_copy.grid(row=0, column=0, padx=5, pady=5)
    btn_open.grid(row=0, column=1, padx=5, pady=5)
    btn_close = tk.Button(
        frame_buttons,
        text=lang["close_telegram"],
        command=close_all_telegram_threaded,
        width=18,
    )
    btn_arrange = tk.Button(
        frame_buttons,
        text=lang["arrange_telegram"],
        command=lambda: arrange_telegram_windows(arrange_width, arrange_height),
        width=18,
    )
    btn_close.grid(row=1, column=0, padx=5, pady=5)
    btn_arrange.grid(row=1, column=1, padx=5, pady=5)
    btn_setting = tk.Button(
        frame_buttons, text="⚙️ Setting", command=open_settings, width=18
    )
    btn_setting.grid(row=2, column=0, padx=5, pady=5)
    mini_chat_l_active = {"status": False}
    from mini_chat import (
        set_root,
        set_mini_chat_globals,
        create_mini_chat,
        destroy_mini_chat,
        create_mini_chatgpt,
        start_mini_chat_monitor,
    )

    def on_mini_chat_l_closed():
        mini_chat_l_active["status"] = False
        btn_mini_chat_l.config(relief=tk.RAISED, text="Mini Chat-L")

    def toggle_mini_chat_l():
        if mini_chat_l_active["status"]:
            destroy_mini_chat()
        else:
            create_mini_chat(on_close=on_mini_chat_l_closed)
            btn_mini_chat_l.config(relief=tk.SUNKEN, text="Tắt Mini Chat-L")
            mini_chat_l_active["status"] = True

    btn_mini_chat_l = tk.Button(
        frame_buttons, text="Mini Chat-L", width=18, command=toggle_mini_chat_l
    )
    btn_mini_chat_l.grid(row=3, column=1, padx=5, pady=5)
    frame_log = tk.Frame(root)
    frame_log.pack(pady=10)
    label_log = tk.Label(frame_log, text=lang["log_label"])
    label_log.pack()
    global text_log
    text_log = tk.Text(frame_log, width=70, height=10)
    text_log.pack()
    saved_path = load_path()
    if saved_path:
        entry_path.insert(0, saved_path)
    footer = tk.Label(root, text=VERSION_INFO, font=("Arial Unicode MS", 8))
    footer.pack(side="bottom", fill="x", pady=5)
    root.protocol("WM_DELETE_WINDOW", on_closing)
    set_root(root)
    set_mini_chat_globals(CHATGPT_API_KEY, TRANSLATION_ONLY, DEFAULT_TARGET_LANG)
    create_mini_chatgpt()
    start_mini_chat_monitor()
    root.mainloop()


def open_telegram_copies():
    """Mở tất cả Telegram portable trong tdata folder và sắp xếp màn hình."""

    def worker():
        results = []
        tdata_dir = entry_path.get()
        if not os.path.exists(tdata_dir):
            root.after(0, lambda: messagebox.showerror("Lỗi", lang["msg_error_path"]))
            return
        tdata_folders = get_tdata_folders(tdata_dir)
        for folder in tdata_folders:
            exe_path = os.path.join(folder, "telegram.exe")
            if os.path.exists(exe_path):
                try:
                    subprocess.Popen([exe_path])
                    results.append(f"Mở thành công: {folder}")
                except Exception as e:
                    results.append(f"Lỗi mở {folder}: {e}")
            else:
                results.append(f"Không tìm thấy exe: {folder}")
            time.sleep(1)
        root.after(
            0, lambda: messagebox.showinfo(lang["msg_open_result"], "\n".join(results))
        )
        time.sleep(1)
        root.after(0, lambda: arrange_telegram_windows(arrange_width, arrange_height))

    threading.Thread(target=worker, daemon=True).start()


def copy_telegram_portable():
    """Placeholder cho tính năng copy Telegram portable."""
    messagebox.showinfo("Copy Telegram", "Tính năng này đang được phát triển.")


def arrange_telegram_windows(custom_width=500, custom_height=504, for_check_live=False):
    """Sắp xếp các cửa sổ Telegram theo dạng lưới/cascade."""
    my_hwnd = root.winfo_id()
    handles = []
    seen_pids = set()

    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
    def enum_callback(hwnd, lParam):
        if hwnd == my_hwnd:
            return True
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            pid = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            process_name = ""
            try:
                if psutil:
                    process = psutil.Process(pid.value)
                    process_name = process.name()
            except:
                pass
            if process_name.lower() == "telegram.exe":
                if for_check_live:
                    handles.append(hwnd)
                else:
                    if pid.value not in seen_pids:
                        seen_pids.add(pid.value)
                        handles.append(hwnd)
        return True

    user32.EnumWindows(enum_callback, 0)
    n = len(handles)
    if n == 0:
        messagebox.showinfo("Arrange", "Không tìm thấy cửa sổ Telegram nào.")
        return
    screen_width = user32.GetSystemMetrics(0)
    screen_height = user32.GetSystemMetrics(1)
    max_cols = screen_width // custom_width
    max_rows = screen_height // custom_height
    if max_cols < 1:
        max_cols = 1
    if max_rows < 1:
        max_rows = 1
    capacity = max_cols * max_rows
    SWP_NOZORDER = 0x0004
    SWP_SHOWWINDOW = 0x0040
    if n <= capacity:
        for index, hwnd in enumerate(handles):
            row = index // max_cols
            col = index % max_cols
            x = col * custom_width
            y = row * custom_height
            user32.SetWindowPos(
                hwnd,
                None,
                x,
                y,
                custom_width,
                custom_height,
                SWP_NOZORDER | SWP_SHOWWINDOW,
            )
            RDW_INVALIDATE = 0x1
            RDW_UPDATENOW = 0x100
            RDW_ALLCHILDREN = 0x80
            user32.RedrawWindow(
                hwnd, None, None, RDW_INVALIDATE | RDW_UPDATENOW | RDW_ALLCHILDREN
            )
            time.sleep(0.1)
    else:
        offset_x = 30
        offset_y = 30
        base_x = 0
        base_y = 0
        for index, hwnd in enumerate(handles):
            x = base_x + (index % capacity) * offset_x
            y = base_y + (index % capacity) * offset_y
            if x + custom_width > screen_width:
                x = screen_width - custom_width
            if y + custom_height > screen_height:
                y = screen_height - custom_height
            user32.SetWindowPos(
                hwnd,
                None,
                x,
                y,
                custom_width,
                custom_height,
                SWP_NOZORDER | SWP_SHOWWINDOW,
            )
            RDW_INVALIDATE = 0x1
            RDW_UPDATENOW = 0x100
            RDW_ALLCHILDREN = 0x80
            user32.RedrawWindow(
                hwnd, None, None, RDW_INVALIDATE | RDW_UPDATENOW | RDW_ALLCHILDREN
            )
            time.sleep(0.1)
    messagebox.showinfo("Arrange", lang["arrange_result"].format(count=n))


# ENTRYPOINT – KHỞI ĐỘNG TOOL
if __name__ == "__main__":
    show_splash_screen()
