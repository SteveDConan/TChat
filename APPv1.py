# ==============================
# appv1.py - MAIN APP MODULE
# ==============================

# --- IMPORT THƯ VIỆN CHUẨN PYTHON ---
import os
import time
import shutil
import subprocess
import asyncio
import math
import ctypes
import threading
import re
import random

# --- IMPORT THƯ VIỆN BỔ SUNG ---
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from tkinter import ttk
import tkinter.font as tkFont
from PIL import Image, ImageChops, ImageTk
import requests
from distutils.version import LooseVersion

# --- THƯ VIỆN NGOÀI NẾU CÓ ---
try:
    from send2trash import send2trash  # Di chuyển thư mục vào thùng rác
except ImportError:
    send2trash = None

try:
    import psutil  # Kiểm tra process còn chạy không
except ImportError:
    psutil = None

from ctypes import wintypes  # Lấy tọa độ cửa sổ

# --- IMPORT TELEGRAM / AUTOIT / LOGIC MODULE ---
from telethon.sync import TelegramClient
from telethon import functions, types, events
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, PhoneCodeExpiredError
from autoit_module import auto_it_function  # Module autoit (tự động hóa thao tác)

# --- IMPORT RESOURCE CẤU HÌNH & TIỆN ÍCH ---
from resources.languages import languages
from resources.config import (
    API_ID, API_HASH, CURRENT_VERSION, GITHUB_USER, GITHUB_REPO,
    CONFIG_FILE, WINDOW_SIZE_FILE, CHATGPT_API_KEY_FILE,
    MARKER_IMAGE_PATH, MARKER_CONFIG_FILE, DEFAULT_TELEGRAM_PATH,
    DEFAULT_TARGET_LANG, TRANSLATION_ONLY, VERSION_INFO
)
from resources.utils import (
    center_window, copy_to_clipboard,
    get_tdata_folders, log_message,
    load_window_size, save_window_size,
    load_chatgpt_api_key, save_chatgpt_api_key,
    read_file, write_file
)

# --- IMPORT CHỨC NĂNG CORE ---
from cores.session import (
    check_authorization, cleanup_session_files, parse_2fa_info, get_otp,
    async_login, login_account
)
from cores.manager import (
    get_tdata_folders, copy_telegram_portable, cleanup_all_sessions,
    count_valid_tdata, status_report, check_folder_exists, check_file_exists
)
from cores.privacy import update_privacy_sync, run_update_privacy_multi
from checklive.marker import show_marker_selection_popup, load_marker_config, save_marker_config
from checklive.compare import capture_window
from checklive.file import load_check_live_status_file, save_check_live_status_file


# Import module vocab_reader
from vocab_reader import open_vocab_reader, close_vocab_reader

# ==============================
# CẤU HÌNH ỨNG DỤNG - BIẾN TOÀN CỤC
# ==============================

CHATGPT_API_KEY = load_chatgpt_api_key(CHATGPT_API_KEY_FILE)
MARKER_IMAGE_PATH = os.path.join(os.getcwd(), "marker_image.png")
MARKER_CONFIG_FILE = os.path.join(os.getcwd(), "marker_config.txt")

arrange_width = 500
arrange_height = 504

user32 = ctypes.windll.user32  # API Windows để thao tác cửa sổ

# Dùng để lưu trạng thái chọn ngôn ngữ, session v.v.
lang = {}
successful_sessions = set()

if not psutil:
    print("Consolog: [CẢNH BÁO] psutil chưa được cài đặt, một số chức năng sẽ không hoạt động!")

# ==============================
# TIỆN ÍCH: LẤY HWND TỪ PID CỦA TELEGRAM
# ==============================
def get_window_handle_by_pid(pid):
    """Tìm HWND của cửa sổ dựa vào PID - dùng để thao tác với Telegram theo từng process."""
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

# ==============================
# HÀM CẢNH BÁO CHECK LIVE
# ==============================
def warn_check_live():
    """Nhắc nhở user đóng tất cả các phiên bản Telegram trước khi check live."""
    warning_msg = (
        "【Tiếng Việt】: Để đảm bảo tính năng Check live hoạt động chính xác và hiệu quả, vui lòng đóng tất cả các phiên bản Telegram đang chạy trên máy tính của bạn. Bạn có muốn đóng chúng ngay bây giờ?\n"
        "【English】: To ensure the Check live feature works accurately and efficiently, please close all running Telegram instances on your computer. Would you like to close them now?\n"
        "【中文】: 为了确保 'Check live' 功能准确高效地运行，请关闭您电脑上所有正在运行的 Telegram 程序。您是否希望立即关闭它们？"
    )
    res = messagebox.askyesno("Cảnh báo", warning_msg)
    if res:
        close_all_telegram_threaded()
    check_live_window()

# ==============================
# TỰ ĐỘNG ĐÓNG TẤT CẢ TELEGRAM (ĐA LUỒNG)
# ==============================
def close_all_telegram_threaded():
    threading.Thread(target=close_all_telegram, daemon=True).start()

def auto_close_telegram():
    """Tự động đóng tất cả tiến trình Telegram đang chạy."""
    print("Consolog: Đang lấy danh sách tiến trình Telegram...")
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq Telegram.exe", "/FO", "CSV"],
            capture_output=True, text=True
        )
        output = result.stdout.strip().splitlines()
        pids = []
        for line in output[1:]:
            parts = line.replace('"', '').split(',')
            if len(parts) >= 2:
                pid = parts[1].strip()
                pids.append(pid)
                print(f"Consolog: Tìm thấy tiến trình Telegram với PID: {pid}")
        for pid in pids:
            print(f"Consolog: Đang đóng tiến trình với PID: {pid}")
            subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True, text=True)
            time.sleep(1)
        # Chờ đến khi tắt sạch
        while True:
            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq Telegram.exe", "/FO", "CSV"],
                capture_output=True, text=True
            )
            lines = result.stdout.strip().splitlines()
            if len(lines) <= 1:
                print("Consolog: Tất cả tiến trình Telegram đã được đóng.")
                break
            print("Consolog: Vẫn còn tiến trình Telegram, chờ 1 giây...")
            time.sleep(1)
        return True
    except Exception as e:
        print(f"Consolog [ERROR]: Lỗi khi tự động tắt Telegram: {e}")
        return False

def close_all_telegram():
    """Đóng tất cả tiến trình Telegram.exe đang chạy trên hệ thống."""
    print("Consolog: Đang đóng tất cả tiến trình Telegram...")
    try:
        result = subprocess.run(["tasklist", "/FI", "IMAGENAME eq Telegram.exe", "/FO", "CSV"], capture_output=True, text=True)
        output = result.stdout.strip().splitlines()
        pids = []
        for line in output[1:]:
            parts = line.replace('"','').split(',')
            if len(parts) >= 2:
                pids.append(parts[1])
        closed = []
        errors = []
        for pid in pids:
            try:
                subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True, text=True)
                closed.append(pid)
                time.sleep(1)
            except Exception as e:
                errors.append(f"PID {pid}: {e}")
        summary = lang["close_result"].format(
            closed=", ".join(closed) if closed else "None",
            errors="; ".join(errors) if errors else "None"
        )
        log_message(summary)
        messagebox.showinfo(lang["close_result_title"], summary)
        print("Consolog: Đóng tiến trình Telegram hoàn tất.")
    except Exception as e:
        messagebox.showerror("Lỗi", f"Không thể đóng các tiến trình Telegram: {e}")

# ======== HẾT PHẦN 1/6 ========

# Khi bạn chat "tiếp", tôi sẽ gửi tiếp PHẦN 2: các nhóm chức năng tiếp theo (xử lý tdata, cập nhật, sắp xếp, tiện ích).
# ==============================
# PHẦN 2/6: QUẢN LÝ TDATA, CẬP NHẬT, LƯU/ĐỌC ĐƯỜNG DẪN
# ==============================

def delete_all_sessions():
    """
    Xóa tất cả các file session của các tài khoản Telegram trong thư mục đã chọn.
    """
    tdata_dir = ""
    try:
        tdata_dir = entry_path.get()
    except Exception:
        pass
    if not os.path.exists(tdata_dir):
        messagebox.showerror("Lỗi", lang.get("msg_error_path", "Không tìm thấy thư mục!"))
        return

    tdata_folders = get_tdata_folders(tdata_dir)
    deleted_accounts = []

    for folder in tdata_folders:
        session_folder = os.path.join(folder, "session")
        session_file = os.path.join(folder, "session.session")
        # Xóa file session
        if os.path.exists(session_file):
            try:
                os.remove(session_file)
                print(f"Consolog: Đã xóa file session {session_file}")
            except Exception as e:
                print(f"Consolog [ERROR]: Lỗi xóa file {session_file}: {e}")
        # Xóa thư mục session
        if os.path.exists(session_folder) and os.path.isdir(session_folder):
            try:
                shutil.rmtree(session_folder)
                print(f"Consolog: Đã xóa thư mục session {session_folder}")
            except Exception as e:
                print(f"Consolog [ERROR]: Lỗi xóa thư mục {session_folder}: {e}")
        deleted_accounts.append(os.path.basename(folder))

    messagebox.showinfo(
        lang.get("popup_inactive_title", "Thông báo"),
        "Đã xóa session của các tài khoản: " + ", ".join(deleted_accounts)
    )
    update_logged()

# ==============================
# CHECK & TẢI CẬP NHẬT MỚI TỪ GITHUB
# ==============================
def check_for_updates():
    """
    Kiểm tra và tải bản cập nhật mới nhất từ GitHub nếu có.
    """
    print("Consolog: Kiểm tra cập nhật phiên bản...")
    try:
        url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/releases/latest"
        response = requests.get(url)
        if response.status_code == 200:
            release_info = response.json()
            latest_version = release_info["tag_name"].lstrip("v")
            print(f"Consolog: Phiên bản mới nhất từ GitHub: {latest_version}")

            if LooseVersion(latest_version) > LooseVersion(CURRENT_VERSION):
                if messagebox.askyesno(
                    "Cập nhật",
                    lang.get("update_available", "Phiên bản {version} có sẵn. Bạn có muốn cập nhật không?").format(version=latest_version)
                ):
                    print("Consolog [UPDATE]: Người dùng chọn cập nhật phiên bản mới.")
                    assets = release_info.get("assets", [])
                    download_url = None
                    for asset in assets:
                        if asset["name"].lower().endswith(".exe"):
                            download_url = asset["browser_download_url"]
                            break
                    if not download_url and assets:
                        download_url = assets[0]["browser_download_url"]

                    if download_url:
                        print(f"Consolog [UPDATE]: Bắt đầu tải file cập nhật từ {download_url}")
                        download_update_with_progress(download_url)
                    else:
                        messagebox.showerror("Error", "Không tìm thấy file cập nhật trên GitHub.")
                        print("Consolog [UPDATE ERROR]: Không tìm thấy asset cập nhật.")
                else:
                    print("Consolog [UPDATE]: Người dùng không cập nhật.")
            else:
                print("Consolog: Bạn đang dùng phiên bản mới nhất.")
        else:
            print("Consolog: Lỗi kiểm tra cập nhật.")
    except Exception as e:
        print(f"Consolog [ERROR]: Lỗi kiểm tra cập nhật: {e}")

def download_update_with_progress(download_url):
    """
    Tải file cập nhật với hiển thị tiến trình tải.
    """
    local_filename = download_url.split("/")[-1]
    print(f"Consolog [UPDATE]: Đang tải xuống file: {local_filename}")

    # Tạo cửa sổ hiển thị tiến trình tải file
    progress_win = tk.Toplevel(root)
    progress_win.title("Đang tải cập nhật")
    progress_win.geometry("550x130")

    style = ttk.Style(progress_win)
    style.configure("Custom.Horizontal.TProgressbar", troughcolor="white", background="blue", thickness=20)

    tk.Label(progress_win, text=f"Đang tải: {local_filename}").pack(pady=5)
    progress_var = tk.DoubleVar(value=0)
    progress_bar = ttk.Progressbar(progress_win, variable=progress_var, maximum=100, length=500, style="Custom.Horizontal.TProgressbar")
    progress_bar.pack(pady=5)
    percent_label = tk.Label(progress_win, text="0%")
    percent_label.pack(pady=5)
    progress_win.update()

    try:
        response = requests.get(download_url, stream=True)
        total_length = response.headers.get('content-length')

        if total_length is None:
            messagebox.showerror("Error", "Không xác định được kích thước file cập nhật.")
            print("Consolog [UPDATE ERROR]: Không xác định được content-length.")
            progress_win.destroy()
            return

        total_length = int(total_length)
        downloaded = 0

        with open(local_filename, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    percent = (downloaded / total_length) * 100
                    progress_var.set(percent)
                    percent_label.config(text=f"{int(percent)}%")
                    progress_win.update_idletasks()
        progress_win.destroy()

        # Hiển thị thông báo tải xong
        notify_win = tk.Toplevel(root)
        notify_win.title("Tải cập nhật thành công")
        tk.Label(notify_win, text=f"Đã tải xong {local_filename}").pack(pady=10)
        def open_update_folder():
            folder = os.path.abspath(os.getcwd())
            try:
                os.startfile(folder)
            except Exception as e:
                messagebox.showerror("Error", f"Lỗi mở thư mục: {e}")

        tk.Button(notify_win, text="Mở vị trí file cập nhật", command=open_update_folder).pack(pady=5)
        tk.Button(notify_win, text="Close", command=notify_win.destroy).pack(pady=5)
        print("Consolog [UPDATE]: Tải về cập nhật hoàn tất.")

    except Exception as e:
        messagebox.showerror("Error", f"Failed to download update: {e}")
        print(f"Consolog [UPDATE ERROR]: Lỗi tải cập nhật: {e}")
        progress_win.destroy()

# ==============================
# TIỆN ÍCH: LƯU/ĐỌC ĐƯỜNG DẪN, CHỌN FOLDER, CẬP NHẬT THỐNG KÊ
# ==============================

def save_path():
    """Lưu đường dẫn được chọn vào file cấu hình (dùng cho thao tác tdata)."""
    folder_path = entry_path.get()
    print(f"Consolog: Lưu đường dẫn: {folder_path}")
    if os.path.exists(folder_path):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write(folder_path)
        messagebox.showinfo("Lưu thành công", lang.get("msg_saved_path", "Đã lưu đường dẫn!"))
        update_stats()
        update_logged()
    else:
        messagebox.showerror("Lỗi", lang.get("msg_error_path", "Thư mục không tồn tại!"))

def load_path():
    """Đọc đường dẫn từ file cấu hình."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            path = f.read().strip()
            print(f"Consolog: Đường dẫn tải được: {path}")
            return path
    return ""

def browse_folder():
    """Hiện hộp thoại chọn thư mục cho user."""
    folder_selected = filedialog.askdirectory()
    print(f"Consolog: Người dùng chọn folder: {folder_selected}")
    entry_path.delete(0, tk.END)
    entry_path.insert(0, folder_selected)

def update_stats():
    """Cập nhật thống kê số lượng tdata trong các thư mục."""
    folder_path = entry_path.get()
    if not os.path.exists(folder_path):
        return
    try:
        subfolders = [d for d in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, d))]
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
    """Cập nhật danh sách các tài khoản đã đăng nhập."""
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
        text_logged.insert(tk.END, lang.get("not_found", "Không tìm thấy!"))
    print("Consolog: Cập nhật logged sessions.")

# ======== HẾT PHẦN 2/6 ========

# Nhập "tiếp" để sang phần 3: các nhóm hàm mở Telegram, thay đổi cài đặt, các tiện ích phụ trợ, các nút thao tác và chuẩn hóa các phần giao diện nhỏ!
# ==============================
# PHẦN 3/6: CHỨC NĂNG MỞ TELEGRAM, THAY ĐỔI, TELETHON, QUYỀN RIÊNG TƯ
# ==============================

def open_telegram_with_tdata(tdata_folder):
    """
    Mở Telegram với tdata folder được chỉ định.
    Args:
        tdata_folder: Đường dẫn đến thư mục tdata.
    Returns:
        Process object nếu mở thành công, None nếu thất bại.
    """
    telegram_exe = os.path.join(tdata_folder, "telegram.exe")
    tdata_sub = os.path.join(tdata_folder, "tdata")
    print(f"Consolog: Mở telegram từ folder: {tdata_folder}")

    if not os.path.exists(telegram_exe):
        log_message(f"Không tìm thấy telegram.exe tại {telegram_exe}")
        return None
    if not os.path.exists(tdata_sub):
        log_message(f"Không tìm thấy thư mục tdata tại {tdata_sub}")
        return None

    log_message(f"🟢 Đang mở {telegram_exe} (cwd={tdata_folder})")
    proc = subprocess.Popen([telegram_exe], cwd=tdata_folder)
    time.sleep(1)
    return proc

def change_account_settings():
    """Thay đổi thông tin tài khoản (đang phát triển, placeholder)."""
    print("Consolog: Yêu cầu thay đổi thông tin tài khoản.")
    messagebox.showinfo("Thông báo", lang.get("change_info_in_development", "Chức năng đang phát triển!"))

def open_telethon_terminal(session_folder):
    """
    Mở terminal Telethon cho một session Telegram.
    Args:
        session_folder: Đường dẫn đến thư mục session.
    """
    phone = os.path.basename(session_folder)
    twofa = parse_2fa_info(session_folder)
    password = twofa.get("password", "N/A")
    print(f"Consolog: Mở phiên Telethon cho {phone} từ session folder: {session_folder}")

    # Cửa sổ terminal mini
    term_win = tk.Toplevel(root)
    term_win.title(lang["telethon_session_title"].format(phone=phone))
    center_window(term_win, 400, 250)

    # Hiển thị thông tin phone
    frame_phone = tk.Frame(term_win)
    frame_phone.pack(pady=5, fill=tk.X)
    lbl_phone = tk.Label(frame_phone, text=f"Phone: {phone}", anchor="w")
    lbl_phone.pack(side=tk.LEFT, expand=True, fill=tk.X)
    btn_copy_phone = tk.Button(frame_phone, text="Copy", command=lambda: copy_to_clipboard(phone))
    btn_copy_phone.pack(side=tk.RIGHT)

    # Hiển thị thông tin password
    frame_pass = tk.Frame(term_win)
    frame_pass.pack(pady=5, fill=tk.X)
    lbl_pass = tk.Label(frame_pass, text=f"Password: {password}", anchor="w")
    lbl_pass.pack(side=tk.LEFT, expand=True, fill=tk.X)
    btn_copy_pass = tk.Button(frame_pass, text="Copy", command=lambda: copy_to_clipboard(password))
    btn_copy_pass.pack(side=tk.RIGHT)

    # Hiển thị OTP
    frame_otp = tk.Frame(term_win)
    frame_otp.pack(pady=5, fill=tk.X, padx=10)
    otp_var = tk.StringVar(value="OTP: ")
    lbl_otp = tk.Label(frame_otp, textvariable=otp_var, anchor="w")
    lbl_otp.pack(side=tk.LEFT, expand=True, fill=tk.X)
    btn_copy_otp = tk.Button(frame_otp, text="Copy", command=lambda: copy_to_clipboard(otp_var.get().replace('OTP: ', '')))
    btn_copy_otp.pack(side=tk.RIGHT)

    def update_otp(new_otp):
        """Cập nhật OTP mới lên label."""
        print(f"Consolog: Cập nhật OTP: {new_otp}")
        otp_var.set(f"OTP: {new_otp}")

    def run_telethon():
        """Khởi tạo phiên Telethon để nghe OTP."""
        async def telethon_session():
            print(f"Consolog: Khởi tạo client từ session folder: {session_folder}")
            client = TelegramClient(os.path.join(session_folder, "session"), API_ID, API_HASH)
            try:
                await client.connect()
                authorized = await client.is_user_authorized()
                print(f"Consolog: Authorized: {authorized}")

                if not authorized:
                    term_win.after(0, update_otp, "Session is NOT authorized!")
                    return

                term_win.after(0, update_otp, "Session authorized - waiting for OTP messages...")

                @client.on(events.NewMessage)
                async def handler(event):
                    text_msg = event.message.message
                    print(f"Consolog: Tin nhắn mới nhận được: {text_msg}")
                    m = re.search(r'\b\d{5,6}\b', text_msg)
                    if m:
                        found_otp = m.group(0)
                        print(f"Consolog: OTP tìm thấy: {found_otp}")
                        term_win.after(0, update_otp, found_otp)

                await client.run_until_disconnected()
            except Exception as e:
                print(f"Consolog [ERROR]: {e}")
                term_win.after(0, update_otp, f"Error: {e}")
            finally:
                await client.disconnect()
                print("Consolog: Client đã ngắt kết nối.")

        asyncio.run(telethon_session())

    threading.Thread(target=run_telethon, daemon=True).start()

def update_privacy(session_path):
    """
    Cập nhật quyền riêng tư cho một session Telegram (ẩn số điện thoại & cuộc gọi).
    """
    async def run_update():
        print(f"Consolog: Đang cập nhật quyền riêng tư cho session: {session_path}")
        client = TelegramClient(session_path, API_ID, API_HASH)
        try:
            await client.connect()
        except Exception as e:
            log_message(f"Consolog [ERROR]: Lỗi kết nối cho {session_path}: {e}")
            return
        try:
            await client(functions.account.SetPrivacyRequest(
                key=types.InputPrivacyKeyPhoneNumber(),
                rules=[types.InputPrivacyValueDisallowAll()]
            ))
            if hasattr(types, "InputPrivacyKeyCalls"):
                await client(functions.account.SetPrivacyRequest(
                    key=types.InputPrivacyKeyCalls(),
                    rules=[types.InputPrivacyValueDisallowAll()]
                ))
            else:
                log_message("Consolog: InputPrivacyKeyCalls không khả dụng, bỏ qua.")
            log_message(f"Consolog: Cập nhật quyền riêng tư thành công cho session {session_path}")
        except Exception as e:
            log_message(f"Consolog [ERROR]: Lỗi cập nhật quyền riêng tư cho session {session_path}: {e}")
        await client.disconnect()

    asyncio.run(run_update())

def run_tool():
    """
    Chạy batch cập nhật quyền riêng tư cho toàn bộ tài khoản.
    """
    print("Consolog: Bắt đầu chạy tính năng cập nhật quyền riêng tư cho tất cả tài khoản.")
    tdata_dir = entry_path.get()
    if not os.path.exists(tdata_dir):
        messagebox.showerror("Lỗi", lang.get("msg_error_path", "Không tìm thấy thư mục!"))
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
            log_message(f"Consolog [ERROR]: Lỗi cập nhật quyền riêng tư cho {folder}: {e}")
    messagebox.showinfo("Hoàn thành", lang.get("msg_privacy_complete", "Đã cập nhật quyền riêng tư!"))
    log_message("Consolog: Đã hoàn tất cập nhật quyền riêng tư.")

# ==============================
# TIỆN ÍCH PHỤ TRỢ VÀ CHỨC NĂNG GIAO DIỆN
# ==============================

def report_function():
    print("Consolog: Report function được gọi.")
    messagebox.showinfo("Report", lang.get("report_in_development", "Chức năng đang phát triển!"))

def warn_auto_it():
    """
    Cảnh báo trước khi chạy chức năng AutoIT, tắt mini chat nếu đang bật.
    """
    try:
        from mini_chat import destroy_mini_chat
        destroy_mini_chat()
        print("Consolog: Mini chat đã được đóng khi bật chức năng AutoIT.")
    except Exception as e:
        print("Consolog [WARNING]: Không thể đóng mini chat:", e)
    warning_msg = (
        "【Tiếng Việt】: Trước khi khởi chạy chức năng AutoIT, chúng tôi khuyến nghị bạn kiểm tra trạng thái trực tiếp của các tài khoản Telegram.\n"
        "【English】: Before initiating the AutoIT function, we strongly recommend performing a live check on your Telegram accounts.\n"
        "【中文】: 在启动 AutoIT 功能之前，我们强烈建议您先对所有 Telegram 账户进行实时检查。"
    )
    messagebox.showinfo("Khuyến cáo", warning_msg)
    auto_it_function(root, entry_path, lang, get_tdata_folders)

# ======== HẾT PHẦN 3/6 ========

# Nhập "tiếp" để sang phần 4: các nhóm chức năng kiểm tra live, snapshot, check marker, bảng quản lý tài khoản live/không live.
# ==============================
# PHẦN 4/6: CHECK LIVE - SO SÁNH ẢNH - QUẢN LÝ TRẠNG THÁI LIVE/NON-LIVE
# ==============================

# Các biến toàn cục phục vụ cho Check Live
check_live_thread = None
check_live_pause_event = threading.Event()
check_live_status = {}
confirm_done = False
tdata_process_map = {}
TEMP_SCREENSHOT_FOLDER = None

def compare_screenshot_with_marker(screenshot, marker_image, threshold=20):
    """
    So sánh ảnh chụp với marker image.
    Args:
        screenshot: Ảnh chụp màn hình.
        marker_image: Ảnh marker để so sánh.
        threshold: Ngưỡng so sánh (càng thấp càng chính xác).
    Returns:
        bool: True nếu ảnh tương tự, False nếu khác biệt.
    """
    print("Consolog: So sánh ảnh chụp với marker image...")
    if screenshot.size != marker_image.size:
        marker_image = marker_image.resize(screenshot.size)
    diff = ImageChops.difference(screenshot, marker_image)
    h = diff.histogram()
    sq = (value * ((idx % 256) ** 2) for idx, value in enumerate(h))
    sum_sq = sum(sq)
    rms = math.sqrt(sum_sq / (screenshot.size[0] * screenshot.size[1]))
    print(f"Consolog: Giá trị RMS = {rms}")
    return rms < threshold

def screenshot_comparison_worker():
    """
    Worker thread để so sánh ảnh chụp màn hình của tất cả cửa sổ Telegram với marker.
    """
    print("Consolog: Luồng so sánh ảnh bắt đầu, chờ 2 giây...")
    time.sleep(2)
    user32 = ctypes.windll.user32
    captured_screenshots = {}

    # Chụp ảnh cho từng tdata
    for tdata_name, pid_list in tdata_process_map.items():
        print(f"Consolog: === BẮT ĐẦU XỬ LÝ TDATA: {tdata_name} ===")
        window_handle = None
        # Tìm handle cửa sổ cho PID
        for pid in pid_list:
            print(f"Consolog: -> Đang lấy HWND cho PID={pid} (TData={tdata_name})")
            try:
                hwnd = get_window_handle_by_pid(int(pid))
                print(f"Consolog: get_window_handle_by_pid({pid}) => {hwnd}")
            except Exception as e:
                print(f"Consolog [ERROR]: Lỗi get_window_handle_by_pid: {e}")
                hwnd = None
            if hwnd:
                window_handle = hwnd
                print(f"Consolog: -> Đã tìm thấy HWND={window_handle} cho PID={pid}, bỏ qua các PID khác.")
                break

        # Chụp ảnh nếu tìm thấy handle
        if window_handle:
            try:
                SW_RESTORE = 9
                user32.ShowWindow(window_handle, SW_RESTORE)
                user32.SetForegroundWindow(window_handle)
                print(f"Consolog: -> Đã gọi ShowWindow/SetForegroundWindow cho HWND={window_handle}")
                time.sleep(0.5)

                rect = wintypes.RECT()
                user32.GetWindowRect(window_handle, ctypes.byref(rect))
                w = rect.right - rect.left
                h = rect.bottom - rect.top
                print(f"Consolog: Kích thước cửa sổ (HWND={window_handle}): ({rect.left}, {rect.top}, {rect.right}, {rect.bottom}) => {w}x{h}")

                screenshot = capture_window(window_handle)
                if screenshot is None:
                    print("Consolog [ERROR]: capture_window trả về None, không chụp được ảnh!")
                else:
                    print(f"Consolog: Đã chụp ảnh thành công (size={screenshot.size}).")

                if screenshot:
                    if TEMP_SCREENSHOT_FOLDER:
                        file_path = os.path.join(TEMP_SCREENSHOT_FOLDER, f"{tdata_name}_screenshot.png")
                        screenshot.save(file_path)
                        print(f"Consolog: Đã lưu ảnh chụp của {tdata_name} tại {file_path}")
                        captured_screenshots[tdata_name] = file_path
            except Exception as e:
                print(f"Consolog [ERROR]: Lỗi chụp ảnh cho {tdata_name} - HWND={window_handle}: {e}")
        else:
            print(f"Consolog: -> Không tìm thấy HWND cho {tdata_name}, đánh dấu not_active.")
            check_live_status[tdata_name]["live"] = lang["not_active"]
        cl_win.after(0, refresh_table_global)

    # Hiển thị popup chọn marker nếu có
    screenshot_paths = list(captured_screenshots.values())
    if screenshot_paths:
        print(f"Consolog: Đã chụp được {len(screenshot_paths)} ảnh, mở popup chọn marker.")
        show_marker_selection_popup(screenshot_paths)
    else:
        print("Consolog: Không có ảnh chụp nào để chọn marker.")

    # So sánh với marker image
    marker_image = None
    if os.path.exists(MARKER_IMAGE_PATH):
        try:
            marker_image = Image.open(MARKER_IMAGE_PATH)
            print("Consolog: Đã mở file marker_image.png để so sánh.")
        except Exception as e:
            print(f"Consolog [ERROR]: Lỗi mở marker image: {e}")

    # So sánh từng ảnh với marker
    for tdata_name, file_path in captured_screenshots.items():
        if marker_image is not None:
            try:
                screenshot = Image.open(file_path)
                print(f"Consolog: So sánh ảnh {file_path} với marker...")
                is_similar = compare_screenshot_with_marker(screenshot, marker_image)
                if is_similar:
                    check_live_status[tdata_name]["live"] = lang["not_active"]
                    print(f"Consolog: {tdata_name} => not_active (gần giống marker).")
                else:
                    check_live_status[tdata_name]["live"] = lang["live"]
                    print(f"Consolog: {tdata_name} => live (khác marker).")
            except Exception as e:
                print(f"Consolog [ERROR]: Lỗi so sánh ảnh cho {tdata_name}: {e}")
        else:
            check_live_status[tdata_name]["live"] = lang["live"]
            print(f"Consolog: Không có marker, đặt mặc định {tdata_name} => live.")

        cl_win.after(0, refresh_table_global)

    print("Consolog: So sánh ảnh hoàn thành.")
    cl_win.after(0, lambda: messagebox.showinfo("Check live", "Đã hoàn thành kiểm tra qua so sánh hình ảnh."))
    cl_win.after(0, lambda: messagebox.showinfo("Check live", "Quá trình mở telegram hoàn tất. Hệ thống sẽ tự động so sánh hình ảnh sau 2 giây."))

def check_live_window():
    """
    Tạo và hiển thị cửa sổ check live.
    """
    global cl_win, refresh_table_global
    cl_win = tk.Toplevel(root)
    cl_win.title(lang["check_live_title"])
    center_window(cl_win, 1200, 500)

    # Frame cấu hình kích thước
    size_frame = tk.Frame(cl_win)
    size_frame.pack(pady=5)
    tk.Label(size_frame, text="Window Width:").grid(row=0, column=0, padx=5)
    entry_width = tk.Entry(size_frame, width=6)
    default_width, default_height = load_window_size(WINDOW_SIZE_FILE)
    entry_width.insert(0, str(default_width))
    entry_width.grid(row=0, column=1, padx=5)

    tk.Label(size_frame, text="Window Height:").grid(row=0, column=2, padx=5)
    entry_height = tk.Entry(size_frame, width=6)
    entry_height.insert(0, str(default_height))
    entry_height.grid(row=0, column=3, padx=5)

    # Load trạng thái check live
    load_check_live_status_file()

    # Tạo bảng hiển thị
    columns = ("stt", "tdata", "check_status", "live_status")
    tree = ttk.Treeview(cl_win, columns=columns, show="headings", height=15)
    tree.heading("stt", text=lang["stt"])
    tree.heading("tdata", text="TData")
    tree.heading("check_status", text=lang["check_status"])
    tree.heading("live_status", text=lang["live_status"])
    tree.column("stt", width=50, anchor="center")
    tree.column("tdata", width=200, anchor="center")
    tree.column("check_status", width=200, anchor="center")
    tree.column("live_status", width=200, anchor="center")
    tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def refresh_table():
        """Cập nhật bảng hiển thị."""
        tree.delete(*tree.get_children())
        tdata_dir = entry_path.get()
        folders = get_tdata_folders(tdata_dir)
        for idx, folder in enumerate(folders, start=1):
            tdata_name = os.path.basename(folder)
            if tdata_name not in check_live_status:
                check_live_status[tdata_name] = {
                    "check": lang["not_checked"],
                    "live": lang["not_checked"]
                }
            row_data = check_live_status[tdata_name]
            tree.insert("", tk.END, values=(idx, tdata_name, row_data["check"], row_data["live"]))
        print("Consolog: Cập nhật bảng check live.")

    refresh_table_global = refresh_table
    refresh_table()

    # ===== NÚT VÀ CHỨC NĂNG ĐIỀU KHIỂN CHECK LIVE =====
    def switch_button_states(running):
        if running:
            btn_start.config(state=tk.DISABLED)
            btn_pause.config(state=tk.NORMAL)
        else:
            btn_start.config(state=tk.NORMAL)
            btn_pause.config(state=tk.DISABLED)

    def start_check_live():
        """Bắt đầu quá trình check live (đa luồng)."""
        global check_live_thread, tdata_process_map, TEMP_SCREENSHOT_FOLDER
        tdata_process_map = {}
        print("Consolog: Bắt đầu quy trình check live...")

        # Tạo thư mục tạm cho ảnh chụp
        TEMP_SCREENSHOT_FOLDER = os.path.join(os.getcwd(), "temp_screenshots")
        if os.path.exists(TEMP_SCREENSHOT_FOLDER):
            shutil.rmtree(TEMP_SCREENSHOT_FOLDER)
        os.makedirs(TEMP_SCREENSHOT_FOLDER, exist_ok=True)
        print(f"Consolog: Tạo thư mục tạm để lưu ảnh chụp tại {TEMP_SCREENSHOT_FOLDER}")

        if check_live_thread and check_live_pause_event.is_set():
            check_live_pause_event.clear()
            switch_button_states(running=True)
            return

        switch_button_states(running=True)

        def worker():
            tdata_dir = entry_path.get()
            folders = get_tdata_folders(tdata_dir)
            for folder in folders:
                while check_live_pause_event.is_set():
                    time.sleep(0.3)
                tdata_name = os.path.basename(folder)
                check_live_status[tdata_name] = {
                    "check": lang["checking"],
                    "live": check_live_status[tdata_name].get("live", lang["not_checked"])
                }
                cl_win.after(0, refresh_table_global)

                exe_path = os.path.join(folder, "telegram.exe")
                if os.path.exists(exe_path):
                    print(f"Consolog: Mở telegram cho TData {tdata_name}")
                    proc = subprocess.Popen([exe_path])
                    pid = proc.pid
                    if tdata_name not in tdata_process_map:
                        tdata_process_map[tdata_name] = []
                    tdata_process_map[tdata_name].append(pid)
                    print(f"Consolog: Lưu PID {pid} cho TData {tdata_name}")
                    time.sleep(1)
                    check_live_status[tdata_name]["check"] = lang["completed"]
                else:
                    check_live_status[tdata_name]["check"] = lang["exe_not_found"]

                cl_win.after(0, refresh_table_global)

            # Lấy kích thước cửa sổ tùy chỉnh
            try:
                custom_width = int(entry_width.get())
            except:
                custom_width = 500
            try:
                custom_height = int(entry_height.get())
            except:
                custom_height = 300
            print(f"Consolog: Sử dụng kích thước cửa sổ tùy chỉnh: {custom_width}x{custom_height}")
            save_window_size(custom_width, custom_height)
            print("Consolog: Đã lưu kích thước cửa sổ.")
            print("Consolog: Đã mở xong tất cả cửa sổ Telegram. Tiến hành sắp xếp cửa sổ...")
            arrange_telegram_windows(custom_width, custom_height, for_check_live=True)
            cl_win.after(0, lambda: messagebox.showinfo(
                "Check live",
                "Quá trình mở telegram hoàn tất.\nHệ thống sẽ tự động so sánh hình ảnh sau 2 giây."
            ))
            threading.Thread(target=screenshot_comparison_worker, daemon=True).start()
            global check_live_thread
            check_live_thread = None

        check_live_thread = threading.Thread(target=worker, daemon=True)
        check_live_thread.start()

    def pause_check_live():
        """Tạm dừng quá trình check live."""
        print("Consolog: Tạm dừng quy trình check live.")
        check_live_pause_event.set()
        switch_button_states(running=False)

    def confirm_check_live():
        """Xác nhận và lưu kết quả check live."""
        print("Consolog: Xác nhận trạng thái check live và lưu vào file.")
        save_check_live_status_file()
        messagebox.showinfo("Check live", "Đã lưu trạng thái check live vào file check_live_status.txt")
        global confirm_done
        confirm_done = True
        btn_copy_inactive.config(state=tk.NORMAL)
        btn_delete_inactive.config(state=tk.NORMAL)
        btn_copy_table.config(state=tk.NORMAL)
        global TEMP_SCREENSHOT_FOLDER
        if TEMP_SCREENSHOT_FOLDER and os.path.exists(TEMP_SCREENSHOT_FOLDER):
            shutil.rmtree(TEMP_SCREENSHOT_FOLDER)
            print(f"Consolog: Đã xóa thư mục tạm {TEMP_SCREENSHOT_FOLDER}")
            TEMP_SCREENSHOT_FOLDER = None

    def copy_table():
        """Copy toàn bộ nội dung bảng."""
        if not confirm_done:
            messagebox.showwarning("Copy Table", "Vui lòng bấm '" + lang["confirm"] + "' trước.")
            return
        table_text = ""
        for child in tree.get_children():
            values = tree.item(child, "values")
            table_text += "\t".join(str(v) for v in values) + "\n"
        root.clipboard_clear()
        root.clipboard_append(table_text)
        root.update()
        messagebox.showinfo("Copy Table", "Đã copy toàn bộ nội dung bảng vào clipboard.")
        print("Consolog: Copy bảng check live thành công.")

    def copy_inactive():
        """Copy danh sách tài khoản không hoạt động."""
        if not confirm_done:
            messagebox.showwarning("Copy Inactive", "Vui lòng bấm '" + lang["confirm"] + "' trước.")
            return
        inactive_list = []
        for child in tree.get_children():
            values = tree.item(child, "values")
            if len(values) >= 4 and values[3] == lang["not_active"]:
                inactive_list.append(values[1])
        if not inactive_list:
            messagebox.showinfo("Copy Inactive", "Không có TData nào ở trạng thái không hoạt động.")
            return
        text_inactive = "\n".join(inactive_list)
        print(f"Consolog: Copy danh sách TData không hoạt động: {text_inactive}")
        root.clipboard_clear()
        root.clipboard_append(text_inactive)
        root.update()
        messagebox.showinfo("Copy Inactive", "Đã copy vào clipboard danh sách TData không hoạt động:\n" + text_inactive)

    def delete_inactive():
        """Xóa các tài khoản không hoạt động."""
        if not confirm_done:
            messagebox.showwarning("Xóa TData", "Vui lòng bấm '" + lang["confirm"] + "' trước.")
            return
        print("Consolog: Đang xóa các TData không hoạt động...")
        auto_close_telegram()
        tdata_dir = entry_path.get()
        folders = get_tdata_folders(tdata_dir)
        deleted = []
        for folder in folders:
            tdata_name = os.path.basename(folder)
            if check_live_status.get(tdata_name, {}).get("live") == lang["not_active"]:
                normalized_folder = os.path.normpath(folder)
                if os.path.exists(normalized_folder):
                    try:
                        print(f"Consolog: Xóa TData không hoạt động: {normalized_folder}")
                        if send2trash:
                            send2trash(normalized_folder)
                        else:
                            shutil.rmtree(normalized_folder)
                        deleted.append(tdata_name)
                        check_live_status.pop(tdata_name, None)
                    except Exception as e:
                        log_message(f"Consolog [ERROR]: Lỗi xóa {normalized_folder}: {e}")
                else:
                    log_message(f"Consolog [ERROR]: Thư mục không tồn tại: {normalized_folder}")
        refresh_table_global()
        messagebox.showinfo("Check live", f"Đã xóa {len(deleted)} thư mục không hoạt động:\n" + ", ".join(deleted))
        save_check_live_status_file()
        print("Consolog: Xóa TData không hoạt động hoàn tất.")

    # ===== FRAME NÚT ĐIỀU KHIỂN =====
    frame_buttons = tk.Frame(cl_win)
    frame_buttons.pack(pady=5)
    btn_start = tk.Button(frame_buttons, text=lang["start"], command=start_check_live, width=20)
    btn_pause = tk.Button(frame_buttons, text=lang["pause"], command=pause_check_live, width=20, state=tk.DISABLED)
    btn_confirm = tk.Button(frame_buttons, text=lang["confirm"], command=confirm_check_live, width=20)
    btn_copy_inactive = tk.Button(frame_buttons, text=lang["copy_inactive"], command=copy_inactive, width=25, state=tk.DISABLED)
    btn_delete_inactive = tk.Button(frame_buttons, text=lang["delete_inactive"], command=delete_inactive, width=25, state=tk.DISABLED)
    btn_copy_table = tk.Button(frame_buttons, text=lang["copy_table"], command=copy_table, width=20, state=tk.DISABLED)

    btn_start.grid(row=0, column=0, padx=5)
    btn_pause.grid(row=0, column=1, padx=5)
    btn_confirm.grid(row=0, column=2, padx=5)
    btn_copy_inactive.grid(row=0, column=3, padx=5)
    btn_delete_inactive.grid(row=0, column=4, padx=5)
    btn_copy_table.grid(row=0, column=5, padx=5)

# ======== HẾT PHẦN 4/6 ========

# Nhập "tiếp" để sang phần 5: Giao diện chính (main UI), setting, splash screen, ngôn ngữ và các entrypoint khởi động tool!
# ==============================
# PHẦN 5/6: GIAO DIỆN CHÍNH, SETTING, SPLASH, NGÔN NGỮ, KHỞI ĐỘNG TOOL
# ==============================

def open_settings():
    """
    Mở cửa sổ cài đặt để tùy chỉnh các thông số.
    Cho phép điều chỉnh: kích thước sắp xếp cửa sổ Telegram, API key ChatGPT, ngôn ngữ dịch mặc định.
    """
    popup = tk.Toplevel(root)
    popup.title("Setting - Tùy chỉnh sắp xếp & ChatGPT")
    center_window(popup, 400, 350)

    # Info hướng dẫn kích thước
    lbl_info = tk.Label(
        popup,
        text="Nhập kích thước cửa sổ sắp xếp:\nx = (số cột) × Custom Width, y = (số hàng) × Custom Height",
        wraplength=380
    )
    lbl_info.pack(pady=10)

    frame_entries = tk.Frame(popup)
    frame_entries.pack(pady=5)

    tk.Label(frame_entries, text="Custom Width:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
    entry_width = tk.Entry(frame_entries, width=10)
    entry_width.insert(0, str(arrange_width))
    entry_width.grid(row=0, column=1, padx=5, pady=5)

    tk.Label(frame_entries, text="Custom Height:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
    entry_height = tk.Entry(frame_entries, width=10)
    entry_height.insert(0, str(arrange_height))
    entry_height.grid(row=1, column=1, padx=5, pady=5)

    # ChatGPT API Key
    tk.Label(popup, text="ChatGPT API Key:").pack(pady=5)
    chatgpt_key_entry = tk.Entry(popup, width=50)
    chatgpt_key_entry.insert(0, load_chatgpt_api_key(CHATGPT_API_KEY_FILE))
    chatgpt_key_entry.pack(pady=5)

    # Default Translation Language
    tk.Label(popup, text="Default Translation Language (Target):").pack(pady=5)
    translation_lang_var = tk.StringVar(value=DEFAULT_TARGET_LANG)
    translation_lang_menu = tk.OptionMenu(popup, translation_lang_var, "vi", "en", "zh")
    translation_lang_menu.pack(pady=5)

    def save_settings():
        """Lưu các cài đặt từ popup."""
        global arrange_width, arrange_height, CHATGPT_API_KEY, DEFAULT_TARGET_LANG
        try:
            w = int(entry_width.get())
            h = int(entry_height.get())
            arrange_width = w
            arrange_height = h
            save_chatgpt_api_key(chatgpt_key_entry.get().strip())
            CHATGPT_API_KEY = chatgpt_key_entry.get().strip()
            DEFAULT_TARGET_LANG = translation_lang_var.get()
            messagebox.showinfo("Setting", "Đã lưu cấu hình sắp xếp, ChatGPT API Key và ngôn ngữ dịch mặc định!")
            popup.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Giá trị không hợp lệ: {e}")

    btn_save = tk.Button(popup, text="Save", command=save_settings)
    btn_save.pack(pady=10)
    popup.transient(root)
    popup.grab_set()
    root.wait_window(popup)

def select_language():
    """
    Hiển thị cửa sổ chọn ngôn ngữ giao diện ban đầu.
    """
    lang_window = tk.Tk()
    lang_window.title(languages["en"]["lang_select_title"])
    center_window(lang_window, 400, 200)
    tk.Label(lang_window, text="Select Language / 选择语言 / Chọn ngôn ngữ:", font=("Arial Unicode MS", 12)).pack(pady=10)
    language_var = tk.StringVar(value="en")
    for code in ["vi", "en", "zh"]:
        tk.Radiobutton(
            lang_window,
            text=languages[code]["lang_" + code],
            variable=language_var,
            value=code,
            font=("Arial Unicode MS", 10)
        ).pack(anchor="w", padx=20)
    tk.Label(lang_window, text=VERSION_INFO, font=("Arial Unicode MS", 8)).pack(pady=5)
    tk.Button(lang_window, text="OK", command=lambda: set_language(language_var, lang_window), font=("Arial Unicode MS", 10)).pack(pady=10)
    lang_window.mainloop()

def set_language(language_var, window):
    """
    Đặt ngôn ngữ được chọn và khởi tạo giao diện chính.
    """
    global lang
    selected = language_var.get()
    lang = languages[selected]
    window.destroy()
    print("Consolog: Người dùng chọn ngôn ngữ xong, khởi tạo giao diện chính.")
    init_main_ui()

def show_splash_screen():
    """
    Hiển thị màn hình splash khi khởi động ứng dụng (giả lập loading...).
    """
    splash = tk.Tk()
    splash.overrideredirect(True)
    width, height = 300, 150
    screen_width = splash.winfo_screenwidth()
    screen_height = splash.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    splash.geometry(f"{width}x{height}+{x}+{y}")
    label = tk.Label(splash, text="Loading, please wait...", font=("Arial Unicode MS", 12))
    label.pack(expand=True)
    print("Consolog: Splash screen hiển thị.")
    # Bắt đầu thread load tool
    threading.Thread(target=lambda: load_tool(splash), daemon=True).start()
    splash.mainloop()

def load_tool(splash):
    """
    Load các thành phần cần thiết của tool (fake loading).
    """
    start_time = time.time()
    print("Consolog: Bắt đầu load tool...")
    time.sleep(2)  # Có thể giảm còn 1-2s cho nhanh
    end_time = time.time()
    print("Consolog: Tool đã load xong sau {:.2f} giây.".format(end_time - start_time))
    splash.after(0, lambda: finish_splash(splash))

def finish_splash(splash):
    """
    Kết thúc splash screen và chuyển sang giao diện chọn ngôn ngữ.
    """
    splash.destroy()
    print("Consolog: Splash screen kết thúc, hiển thị giao diện chọn ngôn ngữ.")
    select_language()

def on_closing():
    """
    Xử lý khi user đóng ứng dụng - dọn session chưa hoàn thành.
    """
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

def init_main_ui():
    """
    Khởi tạo giao diện chính của ứng dụng, các nút chức năng chính/phụ, bảng thống kê, log, footer...
    Mini Chat lớn sẽ chỉ được bật/tắt bằng nút "Mini Chat-L", luôn đồng bộ trạng thái với cửa sổ.
    Mini Chat nhỏ vẫn tự động như trước.
    """
    global root, entry_path, text_stats, text_logged, text_summary, text_log, telegram_path_entry

    # Cửa sổ chính
    root = tk.Tk()
    root.title(lang["title"])
    center_window(root, 650, 800)

    # Cấu hình font mặc định
    default_font = tkFont.nametofont("TkDefaultFont")
    default_font.configure(family="Arial Unicode MS", size=10)
    root.option_add("*Font", default_font)

    # Kiểm tra cập nhật version trong thread riêng
    threading.Thread(target=check_for_updates, daemon=True).start()

    # Tiêu đề
    label_title = tk.Label(root, text=lang["title"], font=("Arial Unicode MS", 14, "bold"))
    label_title.pack(pady=10)

    # Frame đường dẫn (folder chứa Telegram)
    frame_path = tk.Frame(root)
    frame_path.pack(pady=5)
    entry_path = tk.Entry(frame_path, width=50)
    entry_path.pack(side=tk.LEFT, padx=5)
    btn_browse = tk.Button(frame_path, text=lang["choose_folder"], command=browse_folder)
    btn_browse.pack(side=tk.LEFT)

    # Frame đường dẫn Telegram
    frame_telegram_path = tk.Frame(root)
    frame_telegram_path.pack(pady=5)
    tk.Label(frame_telegram_path, text=lang["telegram_path_label"]).pack(side=tk.LEFT, padx=5)
    telegram_path_entry = tk.Entry(frame_telegram_path, width=50)
    telegram_path_entry.insert(0, DEFAULT_TELEGRAM_PATH)
    telegram_path_entry.pack(side=tk.LEFT, padx=5)

    # Nút lưu đường dẫn
    btn_save = tk.Button(root, text=lang["save_path"], command=save_path, width=20)
    btn_save.pack(pady=5)

    # Frame các nút chức năng
    frame_buttons = tk.Frame(root)
    frame_buttons.pack(pady=5)

    def warn_telethon():
        """Cảnh báo trước khi sử dụng Telethon."""
        warning_msg = (
            "【Tiếng Việt】: Chức năng Telethon hiện đang trong giai đoạn thử nghiệm.\n"
            "【English】: The Telethon feature is currently experimental.\n"
            "【中文】: Telegram 功能目前处于实验阶段，请注意可能存在一些问题或不稳定的情况。"
        )
        messagebox.showwarning("Cảnh báo", warning_msg)
        login_all_accounts()

    btn_login_all = tk.Button(frame_buttons, text=lang["login_all"], command=warn_telethon, width=18)
    btn_copy = tk.Button(frame_buttons, text=lang["copy_telegram"], command=lambda: copy_telegram_portable(), width=18)
    btn_open = tk.Button(frame_buttons, text=lang["open_telegram"], command=lambda: open_telegram_copies(), width=18)
    btn_login_all.grid(row=0, column=0, padx=5, pady=5)
    btn_copy.grid(row=0, column=1, padx=5, pady=5)
    btn_open.grid(row=0, column=2, padx=5, pady=5)

    btn_close = tk.Button(frame_buttons, text=lang["close_telegram"], command=close_all_telegram_threaded, width=18)
    btn_arrange = tk.Button(frame_buttons, text=lang["arrange_telegram"], command=lambda: arrange_telegram_windows(arrange_width, arrange_height), width=18)
    btn_auto_it = tk.Button(frame_buttons, text=lang["auto_it"], command=warn_auto_it, width=18)
    btn_close.grid(row=1, column=0, padx=5, pady=5)
    btn_arrange.grid(row=1, column=1, padx=5, pady=5)
    btn_auto_it.grid(row=1, column=2, padx=5, pady=5)

    btn_check_live = tk.Button(frame_buttons, text=lang["check_live"], command=lambda: warn_check_live(), width=18)
    btn_setting = tk.Button(frame_buttons, text="⚙️ Setting", command=open_settings, width=18)
    btn_update = tk.Button(frame_buttons, text=lang["check_update"], command=check_for_updates, width=18)
    btn_check_live.grid(row=2, column=0, padx=5, pady=5)
    btn_setting.grid(row=2, column=1, padx=5, pady=5)
    btn_update.grid(row=2, column=2, padx=5, pady=5)

    # Nút vocab_reader
    btn_read_vocab = tk.Button(frame_buttons, text="Read", width=18)
    btn_read_vocab.grid(row=3, column=0, padx=5, pady=5)
    btn_read_vocab.active = False  # Khởi tạo trạng thái active

    # Trạng thái bật/tắt vocab_reader
    def toggle_vocab_reader():
        if btn_read_vocab.active:
            close_vocab_reader()
            btn_read_vocab.config(relief=tk.RAISED)
            btn_read_vocab.active = False
        else:
            open_vocab_reader(root)
            btn_read_vocab.config(relief=tk.SUNKEN)
            btn_read_vocab.active = True

    btn_read_vocab.config(command=toggle_vocab_reader)

    # ====== Mini Chat-L (LỚN) ĐỒNG BỘ HÓA TRẠNG THÁI ======
    mini_chat_l_active = {"status": False}

    from mini_chat import (
        set_root,
        set_mini_chat_globals,
        create_mini_chat,
        destroy_mini_chat,
        create_mini_chatgpt,
        start_mini_chat_monitor
    )

    def on_mini_chat_l_closed():
        # Callback khi cửa sổ Mini Chat-L bị đóng (bởi user hoặc code)
        mini_chat_l_active["status"] = False
        btn_mini_chat_l.config(relief=tk.RAISED, text="Mini Chat-L")

    def toggle_mini_chat_l():
        if mini_chat_l_active["status"]:
            destroy_mini_chat()
            # Khi destroy_mini_chat gọi xong sẽ tự callback lại nút
        else:
            create_mini_chat(on_close=on_mini_chat_l_closed)  # Truyền callback này vào mini_chat.py
            btn_mini_chat_l.config(relief=tk.SUNKEN, text="Tắt Mini Chat-L")
            mini_chat_l_active["status"] = True

    btn_mini_chat_l = tk.Button(frame_buttons, text="Mini Chat-L", width=18, command=toggle_mini_chat_l)
    btn_mini_chat_l.grid(row=3, column=1, padx=5, pady=5)

    # Thống kê
    frame_stats = tk.Frame(root)
    frame_stats.pack(pady=10)
    label_stats = tk.Label(frame_stats, text=lang["stats_label"])
    label_stats.pack()
    text_stats = tk.Text(frame_stats, width=70, height=10)
    text_stats.pack()
    
    # Tổng kết
    frame_summary = tk.Frame(root)
    frame_summary.pack(pady=10)
    text_summary = tk.Text(frame_summary, width=70, height=5)
    frame_summary.pack_forget()

    # Đã đăng nhập
    frame_logged = tk.Frame(root)
    frame_logged.pack(pady=10)
    global text_logged
    text_logged = tk.Text(frame_logged, width=70, height=5)
    frame_logged.pack_forget()

    # Log
    frame_log = tk.Frame(root)
    frame_log.pack(pady=10)
    label_log = tk.Label(frame_log, text=lang["log_label"])
    label_log.pack()
    global text_log
    text_log = tk.Text(frame_log, width=70, height=10)
    text_log.pack()

    # Load đường dẫn đã lưu
    saved_path = load_path()
    if saved_path:
        entry_path.insert(0, saved_path)
        update_stats()
        update_logged()

    # Footer với thông tin phiên bản
    footer = tk.Label(root, text=VERSION_INFO, font=("Arial Unicode MS", 8))
    footer.pack(side="bottom", fill="x", pady=5)

    root.protocol("WM_DELETE_WINDOW", on_closing)

    # ======= KHỞI ĐỘNG MINI CHAT NHỎ (GẮN TELEGRAM) ========
    set_root(root)
    set_mini_chat_globals(CHATGPT_API_KEY, TRANSLATION_ONLY, DEFAULT_TARGET_LANG)
    # KHÔNG khởi động mini chat lớn ở đây!
    create_mini_chatgpt()
    print("Consolog: Widget Mini Chat nhỏ (gắn vào cửa sổ Telegram) đã được khởi tạo tự động.")
    start_mini_chat_monitor()
    print("Consolog: Giao diện chính được khởi tạo thành công.")

    root.mainloop()



# ======== HẾT PHẦN 5/6 ========

# Nhập "tiếp" để nhận phần cuối (6/6): login_all_accounts, open_telegram_copies, arrange_telegram_windows, cùng các hàm batch còn lại!
# ==============================
# PHẦN 6/6: ĐĂNG NHẬP HÀNG LOẠT, MỞ HÀNG LOẠT, SẮP XẾP CỬA SỔ, TIỆN ÍCH BỔ TRỢ
# ==============================

def login_all_accounts():
    """
    Tạo cửa sổ đăng nhập hàng loạt cho tất cả tài khoản, trình bày trạng thái từng tài khoản, cho phép batch login, batch update privacy...
    """
    print("Consolog: Khởi tạo cửa sổ đăng nhập cho tất cả tài khoản...")
    login_window = tk.Toplevel(root)
    login_window.title(lang["login_window_title"])
    center_window(login_window, 550, 600)

    # Bảng đã đăng nhập
    frame_already = tk.Frame(login_window)
    frame_already.pack(padx=10, pady=5, fill=tk.BOTH, expand=False)
    tk.Label(frame_already, text=lang["logged_accounts"], font=("Arial Unicode MS", 10, "bold")).pack(anchor="w")
    already_tree = ttk.Treeview(frame_already, columns=("account",), show="headings", height=5)
    already_tree.heading("account", text=lang["logged_accounts"])
    already_tree.column("account", width=300)
    already_tree.pack(fill=tk.BOTH, expand=True)
    def update_already_table():
        already_tree.delete(*already_tree.get_children())
        tdata_dir = entry_path.get()
        for folder in get_tdata_folders(tdata_dir):
            session_file = os.path.join(folder, "session.session")
            session_folder = os.path.join(folder, "session")
            if os.path.exists(session_file) or os.path.exists(session_folder):
                already_tree.insert("", tk.END, values=(os.path.basename(folder),))
    update_already_table()

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
            print(f"Consolog: Mở phiên Telethon cho session: {selected_session['path']}")
            open_telethon_terminal(selected_session["path"])
        else:
            messagebox.showwarning("Warning", "Chưa chọn session nào.")
    btn_open_telethon.config(command=open_telethon_action)

    # Tìm các tài khoản cần đăng nhập
    tdata_dir = entry_path.get()
    all_tdata_folders = get_tdata_folders(tdata_dir)
    login_tdata_folders = [
        folder for folder in all_tdata_folders
        if not (os.path.exists(os.path.join(folder, "session.session")) or os.path.exists(os.path.join(folder, "session")))
    ]
    accounts = [os.path.basename(folder) for folder in login_tdata_folders]
    total = len(accounts)
    print(f"Consolog: Có {total} tài khoản cần đăng nhập.")

    # Bảng cần đăng nhập
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

    # Progressbar
    progress_frame = tk.Frame(login_window)
    progress_frame.pack(padx=10, pady=5, fill=tk.X)
    progress_var = tk.DoubleVar(value=0)
    progress_bar = ttk.Progressbar(progress_frame, variable=progress_var, maximum=100)
    progress_bar.pack(fill=tk.X, expand=True)
    progress_label = tk.Label(progress_frame, text="0%")
    progress_label.pack()

    # Các nút chức năng batch login
    frame_buttons_new = tk.Frame(login_window)
    frame_buttons_new.pack(pady=5)
    btn_create_session = tk.Button(frame_buttons_new, text=lang["create_session"], font=("Arial Unicode MS", 10, "bold"))
    btn_update_privacy = tk.Button(frame_buttons_new, text=lang["update_privacy"], font=("Arial Unicode MS", 10, "bold"), command=run_tool)
    btn_change_info = tk.Button(frame_buttons_new, text=lang["change_info"], font=("Arial Unicode MS", 10, "bold"), command=change_account_settings)
    btn_create_session.pack(side=tk.LEFT, padx=5)
    btn_update_privacy.pack(side=tk.LEFT, padx=5)
    btn_change_info.pack(side=tk.LEFT, padx=5)

    btn_delete_all = tk.Button(login_window, text=lang["popup_inactive_delete"], font=("Arial Unicode MS", 10, "bold"), command=delete_all_sessions)
    btn_delete_all.pack(pady=5)

    # Hàm cập nhật trạng thái từng dòng
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

    def process_accounts():
        print("Consolog: Bắt đầu xử lý đăng nhập các tài khoản...")
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
            result = login_account(folder, update_item)
            if result:
                login_success.append(acc)
            else:
                login_failure.append(acc)
            processed += 1
            percent = (processed / total) * 100
            login_window.after(0, progress_var.set, percent)
            login_window.after(0, progress_label.config, {"text": f"{int(percent)}%"})
            time.sleep(0.5)
        login_window.after(0, update_already_table)
        summary = (
            f"{lang['already_logged']}: {len([a for a in accounts if tree.item(a)['values'][1]==lang['skipped']])}\n"
            f"{lang['success']}: {len(login_success)}\n"
            f"{lang['failure']}: {len(login_failure)}\n"
        )
        print("Consolog: Hoàn thành đăng nhập, tổng kết:")
        print(summary)
        login_window.after(0, messagebox.showinfo, "Hoàn thành", lang["msg_login_complete"])
        login_window.after(0, close_all_telegram_threaded)

    def start_login_process():
        btn_create_session.config(state=tk.DISABLED)
        threading.Thread(target=process_accounts, daemon=True).start()
    btn_create_session.config(command=start_login_process)

def open_telegram_copies():
    """
    Mở tất cả các Telegram portable trong tdata folder và sắp xếp chúng lên màn hình.
    """
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
        root.after(0, lambda: messagebox.showinfo(lang["msg_open_result"], "\n".join(results)))
        time.sleep(1)
        root.after(0, lambda: arrange_telegram_windows(arrange_width, arrange_height))
    threading.Thread(target=worker, daemon=True).start()

def copy_telegram_portable():
    """
    Chức năng copy Telegram portable - giả định thực hiện backup/copy sang thư mục khác (tùy ý).
    """
    print("Consolog: Copy Telegram portable - placeholder.")
    messagebox.showinfo("Copy Telegram", "Tính năng này đang được phát triển.")

def arrange_telegram_windows(custom_width=500, custom_height=504, for_check_live=False):
    """
    Sắp xếp các cửa sổ Telegram theo dạng lưới hoặc cascade.
    Args:
        custom_width: Chiều rộng tùy chỉnh cho mỗi cửa sổ.
        custom_height: Chiều cao tùy chỉnh cho mỗi cửa sổ.
        for_check_live: True nếu đang trong chế độ check live.
    """
    print(f"Consolog: [CHANGE] Sắp xếp cửa sổ Telegram (mái ngói) với kích thước {custom_width}x{custom_height}... For check live: {for_check_live}")
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
    print(f"Consolog: [CHANGE] Tìm thấy {n} cửa sổ Telegram.")
    if n == 0:
        messagebox.showinfo("Arrange", "Không tìm thấy cửa sổ Telegram nào.")
        return

    # Tính toán số cột và hàng tối đa
    screen_width = user32.GetSystemMetrics(0)
    screen_height = user32.GetSystemMetrics(1)
    max_cols = screen_width // custom_width
    max_rows = screen_height // custom_height
    if max_cols < 1: max_cols = 1
    if max_rows < 1: max_rows = 1
    capacity = max_cols * max_rows
    SWP_NOZORDER = 0x0004
    SWP_SHOWWINDOW = 0x0040

    # Sắp xếp lưới nếu số lượng <= capacity, còn lại cascade
    if n <= capacity:
        for index, hwnd in enumerate(handles):
            row = index // max_cols
            col = index % max_cols
            x = col * custom_width
            y = row * custom_height
            user32.SetWindowPos(hwnd, None, x, y, custom_width, custom_height, SWP_NOZORDER | SWP_SHOWWINDOW)
            RDW_INVALIDATE = 0x1
            RDW_UPDATENOW = 0x100
            RDW_ALLCHILDREN = 0x80
            user32.RedrawWindow(hwnd, None, None, RDW_INVALIDATE | RDW_UPDATENOW | RDW_ALLCHILDREN)
            time.sleep(0.1)
    else:
        # Cascade
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
            user32.SetWindowPos(hwnd, None, x, y, custom_width, custom_height, SWP_NOZORDER | SWP_SHOWWINDOW)
            RDW_INVALIDATE = 0x1
            RDW_UPDATENOW = 0x100
            RDW_ALLCHILDREN = 0x80
            user32.RedrawWindow(hwnd, None, None, RDW_INVALIDATE | RDW_UPDATENOW | RDW_ALLCHILDREN)
            time.sleep(0.1)
    messagebox.showinfo("Arrange", lang["arrange_result"].format(count=n))

# ==============================
# TIỆN ÍCH GIAO DIỆN BỔ TRỢ
# ==============================
def save_path():
    """Lưu đường dẫn được chọn vào file cấu hình"""
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
    """Đọc đường dẫn từ file cấu hình"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            path = f.read().strip()
            print(f"Consolog: Đường dẫn tải được: {path}")
            return path
    return ""

def browse_folder():
    """Mở dialog chọn thư mục"""
    folder_selected = filedialog.askdirectory()
    print(f"Consolog: Người dùng chọn folder: {folder_selected}")
    entry_path.delete(0, tk.END)
    entry_path.insert(0, folder_selected)

def update_stats():
    """Cập nhật thống kê số lượng tdata trong các thư mục"""
    folder_path = entry_path.get()
    if not os.path.exists(folder_path):
        return
    try:
        subfolders = [d for d in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, d))]
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
    """Cập nhật danh sách các tài khoản đã đăng nhập"""
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

# ==============================
# ENTRYPOINT - KHỞI ĐỘNG TOOL
# ==============================
if __name__ == "__main__":
    print("Consolog: Ứng dụng khởi chạy, hiển thị splash screen để load tool theo thời gian load thực.")
    show_splash_screen()
