import os
import sys
import json
import openai
import hashlib
import threading
import time
import tkinter as tk
from tkinter import messagebox
import ctypes
from ctypes import wintypes
import math
import shutil
import re

# Import phụ thuộc ngoài (được kiểm tra ImportError)
try:
    import psutil
except ImportError:
    psutil = None

from langdetect import detect
from .vocab_widget import VocabWidget

# ========== CẤU HÌNH & BIẾN TOÀN CỤC ==========

root = None
CHATGPT_API_KEY = None
TRANSLATION_ONLY = True
DEFAULT_TARGET_LANG = "en"

MY_LANG_SELECTION = "vi"
TARGET_LANG_SELECTION = DEFAULT_TARGET_LANG
DPI_ENABLED = True

mini_chat_paused = False
mini_chat_pause_button = None
mini_chat_last_active_time = time.time()

mini_chatgpt_win = None
mini_chatgpt_entry = None
mini_chatgpt_pause_button = None

last_valid_telegram_hwnd = None
widget_mini_chat_thread_running = True
mini_chat_on_close_callback = None

LANG_CODE_TO_NAME = {
    "en": "English",
    "zh": "Chinese",
    "vi": "Vietnamese",
    "ar": "Arabic-Egypt",
    "bn": "Bangladesh",
    "pt": "Brazil",
    "am": "Ethiopia",
    "fr": "French",
    "de": "German",
    "id": "Indonesian",
    "km": "Khmer",
    "es": "Spanish-Mexico",
    "tl": "Philippines",
    "yo": "Nigeria",
}
NAME_TO_LANG_CODE = {name: code for code, name in LANG_CODE_TO_NAME.items()}

if "target_lang_display_var" not in globals():
    target_lang_display_var = tk.StringVar(
        value=LANG_CODE_TO_NAME.get(TARGET_LANG_SELECTION, "English")
    )

# ========== HÀM CẤU HÌNH ==========


def set_root(r):
    global root
    root = r


def set_mini_chat_globals(api_key, translation_only_flag, default_lang):
    global CHATGPT_API_KEY, TRANSLATION_ONLY, DEFAULT_TARGET_LANG
    CHATGPT_API_KEY = api_key
    TRANSLATION_ONLY = translation_only_flag
    DEFAULT_TARGET_LANG = default_lang


def load_config():
    global MY_LANG_SELECTION, TARGET_LANG_SELECTION, DPI_ENABLED
    config_file = os.path.join(os.getcwd(), "config.ini")
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or "=" not in line:
                        continue
                    key, value = line.split("=", 1)
                    if key == "MY_LANG_SELECTION":
                        MY_LANG_SELECTION = value
                    elif key == "TARGET_LANG_SELECTION":
                        TARGET_LANG_SELECTION = value
                    elif key == "DPI_ENABLED":
                        DPI_ENABLED = value.lower() == "true"
        except Exception:
            pass


load_config()

mini_chat_win = None
mini_chat_text = None
mini_chat_entry = None
screenshot_images = {}
translation_logs = {}
hwnd_target_lang = {}

user32 = ctypes.windll.user32

# ========== TIẾP THEO LÀ PHẦN HÀM MINI CHAT ==========


def toggle_mini_chat_pause():
    global mini_chat_paused, mini_chat_pause_button, mini_chatgpt_pause_button
    mini_chat_paused = not mini_chat_paused
    if mini_chat_pause_button:
        mini_chat_pause_button.config(text="Resume" if mini_chat_paused else "Pause")
    if mini_chatgpt_pause_button:
        mini_chatgpt_pause_button.config(text="Resume" if mini_chat_paused else "Pause")
    append_mini_chat(
        "Mini Chat đã được tạm dừng."
        if mini_chat_paused
        else "Mini Chat đã được phục hồi."
    )


def create_mini_chat(on_close=None):
    global mini_chat_win, mini_chat_text, mini_chat_entry
    global TARGET_LANG_SELECTION, MY_LANG_SELECTION, DPI_ENABLED, mini_chat_pause_button
    global mini_chat_on_close_callback, target_lang_display_var

    if mini_chat_win is not None:
        mini_chat_win.lift()
        return

    mini_chat_on_close_callback = on_close
    if root is None:
        return

    mini_chat_win = tk.Toplevel(root)
    mini_chat_win.title("Mini Chat")
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    width, height = 530, 350
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    mini_chat_win.geometry(f"{width}x{height}+{x}+{y}")
    mini_chat_win.attributes("-topmost", True)
    threading.Thread(
        target=lambda: (time.sleep(0.5), mini_chat_win.attributes("-topmost", False)),
        daemon=True,
    ).start()

    menu_frame = tk.Frame(mini_chat_win)
    menu_frame.pack(side=tk.TOP, fill=tk.X, pady=5)
    # My Language dropdown
    tk.Label(menu_frame, text="My Language:").pack(side=tk.LEFT, padx=5)
    my_lang_display_var = tk.StringVar(
        value=LANG_CODE_TO_NAME.get(MY_LANG_SELECTION, "Vietnamese")
    )
    my_lang_display_options = list(LANG_CODE_TO_NAME.values())
    my_lang_menu = tk.OptionMenu(
        menu_frame,
        my_lang_display_var,
        *my_lang_display_options,
        command=lambda chosen: update_my_lang(chosen),
    )
    my_lang_menu.pack(side=tk.LEFT, padx=5)
    # Target Language dropdown
    tk.Label(menu_frame, text="Target Language:").pack(side=tk.LEFT, padx=5)
    target_lang_menu = tk.OptionMenu(
        menu_frame,
        target_lang_display_var,
        *my_lang_display_options,
        command=lambda chosen: update_target_lang(chosen),
    )
    target_lang_menu.pack(side=tk.LEFT, padx=5)
    # DPI checkbox
    dpi_var = tk.BooleanVar(value=DPI_ENABLED)
    tk.Checkbutton(
        menu_frame,
        text="Enable DPI",
        variable=dpi_var,
        command=lambda: update_dpi(dpi_var),
    ).pack(side=tk.LEFT, padx=5)

    # Text area
    text_frame = tk.Frame(mini_chat_win)
    text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    mini_chat_text = tk.Text(text_frame, wrap=tk.WORD, state=tk.DISABLED)
    mini_chat_text.pack(fill=tk.BOTH, expand=True)

    # Input area
    frame_input = tk.Frame(mini_chat_win)
    frame_input.pack(fill=tk.X, padx=5, pady=5)
    mini_chat_entry = tk.Entry(frame_input)
    mini_chat_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
    mini_chat_entry.bind("<Return>", lambda e: send_mini_chat_message())
    btn_send = tk.Button(frame_input, text="Send", command=send_mini_chat_message)
    btn_send.pack(side=tk.LEFT, padx=5)
    mini_chat_pause_button = tk.Button(
        frame_input, text="Pause", command=toggle_mini_chat_pause
    )
    mini_chat_pause_button.pack(side=tk.LEFT, padx=5)
    btn_clear = tk.Button(frame_input, text="Clear", command=clear_mini_chat)
    btn_clear.pack(side=tk.LEFT, padx=5)

    def on_closing():
        global mini_chat_win
        if mini_chat_on_close_callback:
            mini_chat_on_close_callback()
        mini_chat_win.destroy()
        mini_chat_win = None

    mini_chat_win.protocol("WM_DELETE_WINDOW", on_closing)
    threading.Thread(target=mini_chat_inactivity_monitor, daemon=True).start()
    threading.Thread(target=track_telegram_window, daemon=True).start()


def update_my_lang(chosen_name):
    global MY_LANG_SELECTION
    MY_LANG_SELECTION = NAME_TO_LANG_CODE[chosen_name]


def update_target_lang(chosen_name):
    global TARGET_LANG_SELECTION
    TARGET_LANG_SELECTION = NAME_TO_LANG_CODE[chosen_name]
    target_lang_display_var.set(chosen_name)
    hwnd = get_correct_telegram_hwnd()
    if hwnd:
        hwnd_target_lang[hwnd] = TARGET_LANG_SELECTION


def update_dpi(dpi_var):
    global DPI_ENABLED
    DPI_ENABLED = dpi_var.get()


def clear_mini_chat():
    global mini_chat_text
    if mini_chat_text is not None:
        mini_chat_text.config(state=tk.NORMAL)
        mini_chat_text.delete("1.0", tk.END)
        mini_chat_text.config(state=tk.DISABLED)


def append_mini_chat(text):
    global mini_chat_text
    if mini_chat_text is None:
        return
    mini_chat_text.config(state=tk.NORMAL)
    mini_chat_text.insert(tk.END, text + "\n")
    mini_chat_text.see(tk.END)
    mini_chat_text.config(state=tk.DISABLED)
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    width, height = 530, 350
    x = screen_width - width - 10
    y = screen_height - height - 10
    mini_chat_win.geometry(f"{width}x{height}+{x}+{y}")
    mini_chat_win.deiconify()
    mini_chat_win.lift()


def on_mini_chat_closed():
    global mini_chat_win, mini_chat_on_close_callback
    if mini_chat_win is not None:
        try:
            mini_chat_win.destroy()
        except Exception:
            pass
        mini_chat_win = None
    if mini_chat_on_close_callback:
        mini_chat_on_close_callback()
        mini_chat_on_close_callback = None


# ... (tiếp tục các hàm dịch, gửi telegram, và các tiện ích trong phần 3)
def translate_text_via_chatgpt(
    text, source_lang="auto", target_lang="en", conversation_context=""
):
    global CHATGPT_API_KEY
    print(f"[DEBUG] API Key: {CHATGPT_API_KEY[:10]}...")
    if not CHATGPT_API_KEY:
        print("Mini Chat [ERROR]: ChatGPT API key not set.")
        return None, None

    try:
        import openai
        print(f"[DEBUG] Bắt đầu dịch: {text}")
        print(f"[DEBUG] Ngôn ngữ đích: {target_lang}")

        openai.api_key = CHATGPT_API_KEY
        lang_map = {
            "vi": "tiếng Việt",
            "en": "tiếng Anh",
            "zh": "tiếng Trung",
            "km": "tiếng Khmer",
            "pt": "tiếng Bồ Đào Nha",
            "bn": "tiếng Bengal",
            "tl": "tiếng Tagalog",
            "am": "tiếng Amhara",
            "ar": "tiếng Ả Rập",
            "es": "tiếng Tây Ban Nha",
            "id": "tiếng Indonesia",
            "yo": "tiếng Yoruba-Nigeria",
        }
        lang_name = lang_map.get(target_lang.lower(), target_lang)
        prompt = (
            f"Hãy chuyển ngữ đoạn văn nằm giữa hai dấu ---START--- và ---END--- dưới đây sang {lang_name} một cách chính xác, tự nhiên và sát nghĩa nhất, "
            f"giống như khi ChatGPT dịch trực tiếp trên nền tảng web. ...\n"
            f"Nội dung cần dịch nằm giữa hai dấu sau:\n---START---\n{text}\n---END---\n\n"
            f"Bối cảnh: {conversation_context}.\nChỉ in kết quả cuối cùng là văn bản đã chuyển ngữ."
            f"Hãy đảm bảo ngôn ngữ đích là {lang_name}."
        )
        print("[DEBUG] Đang gửi request đến ChatGPT...")
        print(f"[DEBUG] Prompt: {prompt}")
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
        )
        full_reply = response.choices[0].message.content.strip()
        print(f"[DEBUG] Phản hồi từ ChatGPT: {full_reply}")
        
        if not full_reply:
            print("Mini Chat [ERROR]: Không nhận được phản hồi từ ChatGPT")
            return None, None
            
        new_full_reply = re.sub(
            r"^(Chuyển\s+ngữ\s+sang\s+.+?:\s*)", "", full_reply, flags=re.IGNORECASE
        )
        if new_full_reply != full_reply:
            full_reply = new_full_reply
            print(f"[DEBUG] Sau khi xóa prefix: {full_reply}")
            
        matches = list(
            re.finditer(
                r"\[(?:Ngôn\s*ngữ|Language):\s*(.*?)\]", full_reply, re.IGNORECASE
            )
        )
        if matches:
            detected_lang = matches[-1].group(1).strip()
            translated_text = full_reply[matches[-1].end() :].strip()
            print(f"[DEBUG] Phát hiện ngôn ngữ: {detected_lang}")
            print(f"[DEBUG] Văn bản sau khi xử lý: {translated_text}")
        else:
            detected_lang = None
            translated_text = full_reply.strip()
            print(f"[DEBUG] Không phát hiện được ngôn ngữ, sử dụng toàn bộ văn bản: {translated_text}")
            
        if not translated_text:
            print("Mini Chat [ERROR]: Không thể trích xuất văn bản đã dịch")
            return None, None
            
        return translated_text, detected_lang
    except openai.APIError as e:
        print(f"Mini Chat [ERROR]: OpenAI API error: {e}")
        return None, None
    except Exception as e:
        print(f"Mini Chat [ERROR]: Translation error: {e}")
        return None, None


def send_message_to_telegram_input(hwnd, message):
    rect = ctypes.wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    width = rect.right - rect.left
    x = rect.left + width // 2
    y = rect.bottom - 3
    ctypes.windll.user32.SetCursorPos(x, y)
    time.sleep(0.1)
    ctypes.windll.user32.mouse_event(2, 0, 0, 0, 0)
    time.sleep(0.05)
    ctypes.windll.user32.mouse_event(4, 0, 0, 0, 0)
    time.sleep(0.1)
    root.clipboard_clear()
    root.clipboard_append(message)
    root.update()
    time.sleep(0.1)
    VK_CONTROL = 0x11
    VK_V = 0x56
    VK_RETURN = 0x0D
    ctypes.windll.user32.keybd_event(VK_CONTROL, 0, 0, 0)
    time.sleep(0.05)
    ctypes.windll.user32.keybd_event(VK_V, 0, 0, 0)
    time.sleep(0.05)
    ctypes.windll.user32.keybd_event(VK_V, 0, 2, 0)
    time.sleep(0.05)
    ctypes.windll.user32.keybd_event(VK_CONTROL, 0, 2, 0)
    time.sleep(0.1)
    ctypes.windll.user32.keybd_event(VK_RETURN, 0, 0, 0)
    time.sleep(0.05)
    ctypes.windll.user32.keybd_event(VK_RETURN, 0, 2, 0)
    time.sleep(0.1)


def get_correct_telegram_hwnd():
    global last_valid_telegram_hwnd
    hwnd_fore = user32.GetForegroundWindow()
    pid = ctypes.wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd_fore, ctypes.byref(pid))
    try:
        proc = psutil.Process(pid.value)
        if proc.name().lower() == "telegram.exe" and not user32.IsIconic(hwnd_fore):
            last_valid_telegram_hwnd = hwnd_fore
            return hwnd_fore
    except Exception:
        pass
    if last_valid_telegram_hwnd and not user32.IsIconic(last_valid_telegram_hwnd):
        return last_valid_telegram_hwnd
    hwnd_result = None
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)

    def enum_windows_proc(hwnd, lParam):
        nonlocal hwnd_result
        if user32.IsWindowVisible(hwnd) and not user32.IsIconic(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            pid_local = ctypes.wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid_local))
            try:
                proc = psutil.Process(pid_local.value)
                if proc.name().lower() == "telegram.exe":
                    hwnd_result = hwnd
                    last_valid_telegram_hwnd = hwnd
                    return False
            except Exception:
                pass
        return True

    enum_proc_c = EnumWindowsProc(enum_windows_proc)
    user32.EnumWindows(enum_proc_c, 0)
    return hwnd_result


def detect_language_by_hwnd(hwnd):
    try:
        target_lang = hwnd_target_lang.get(hwnd, TARGET_LANG_SELECTION)
        return target_lang
    except Exception:
        return DEFAULT_TARGET_LANG


def capture_window(hwnd):
    if DPI_ENABLED:
        ctypes.windll.user32.SetProcessDPIAware()
    user32.ShowWindow(hwnd, 9)
    time.sleep(0.2)
    gdi32 = ctypes.windll.gdi32
    rect = ctypes.wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    width = rect.right - rect.left
    height = rect.bottom - rect.top
    hwindc = user32.GetWindowDC(hwnd)
    srcdc = gdi32.CreateCompatibleDC(hwindc)
    bmp = gdi32.CreateCompatibleBitmap(hwindc, width, height)
    gdi32.SelectObject(srcdc, bmp)
    result = user32.PrintWindow(hwnd, srcdc, 0)

    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [
            ("biSize", ctypes.c_uint32),
            ("biWidth", ctypes.c_int32),
            ("biHeight", ctypes.c_int32),
            ("biPlanes", ctypes.c_uint16),
            ("biBitCount", ctypes.c_uint16),
            ("biCompression", ctypes.c_uint32),
            ("biSizeImage", ctypes.c_uint32),
            ("biXPelsPerMeter", ctypes.c_int32),
            ("biYPelsPerMeter", ctypes.c_int32),
            ("biClrUsed", ctypes.c_uint32),
            ("biClrImportant", ctypes.c_uint32),
        ]

    bmi = BITMAPINFOHEADER()
    bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.biWidth = width
    bmi.biHeight = -height
    bmi.biPlanes = 1
    bmi.biBitCount = 32
    bmi.biCompression = 0
    buffer_len = width * height * 4
    buffer = ctypes.create_string_buffer(buffer_len)
    _ = gdi32.GetDIBits(srcdc, bmp, 0, height, buffer, ctypes.byref(bmi), 0)
    from PIL import Image

    image = Image.frombuffer("RGBA", (width, height), buffer, "raw", "BGRA", 0, 1)
    img_width, img_height = image.size
    if img_width != width or img_height != height:
        gdi32.DeleteObject(bmp)
        gdi32.DeleteDC(srcdc)
        user32.ReleaseDC(hwnd, hwindc)
        from PIL import ImageGrab

        image = ImageGrab.grab(bbox=(rect.left, rect.top, rect.right, rect.bottom))
    else:
        gdi32.DeleteObject(bmp)
        gdi32.DeleteDC(srcdc)
        user32.ReleaseDC(hwnd, hwindc)
    return image


def send_mini_chat_message():
    global mini_chat_entry, mini_chat_text, hwnd_target_lang, TARGET_LANG_SELECTION, mini_chat_paused, mini_chat_last_active_time
    if mini_chat_entry is None:
        return
    mini_chat_last_active_time = time.sleep(0.1)
    if mini_chat_paused:
        mini_chat_paused = False
        if mini_chat_pause_button:
            mini_chat_pause_button.config(text="Pause")
        print("Mini Chat auto resumed do có thao tác từ người dùng.")
    msg = mini_chat_entry.get().strip()
    if not msg:
        return
    mini_chat_entry.delete(0, tk.END)
    print("You: " + msg)
    hwnd = get_correct_telegram_hwnd()
    if hwnd is None:
        print("Mini Chat [ERROR]: Không tìm thấy cửa sổ Telegram đang active.")
        return
    target_lang = hwnd_target_lang.get(hwnd)
    if not target_lang:
        target_lang = TARGET_LANG_SELECTION
        hwnd_target_lang[hwnd] = TARGET_LANG_SELECTION
    print(f"[DEBUG] Đang dịch sang ngôn ngữ: {target_lang}")
    translated, detected = translate_text_via_chatgpt(
        msg, source_lang="auto", target_lang=target_lang
    )
    if translated is None:
        print("Mini Chat [ERROR]: Không thể dịch tin nhắn. Vui lòng thử lại.")
        return
        
    print(f"Translated: {translated}")
    try:
        send_message_to_telegram_input(hwnd, translated)
        time.sleep(0.1)
        if mini_chat_win:
            mini_chat_win.lift()
        if mini_chat_entry:
            mini_chat_entry.focus_force()
    except Exception as e:
        print(f"Mini Chat [ERROR]: Lỗi gửi tin nhắn: {e}")


def mini_chat_monitor():
    TEMP_FOLDER = os.path.join(os.getcwd(), "mini_chat_screenshots")
    os.makedirs(TEMP_FOLDER, exist_ok=True)
    while True:
        try:
            if mini_chat_paused:
                time.sleep(3)
                continue
            time.sleep(3)
            hwnd_fore = user32.GetForegroundWindow()
            pid = ctypes.wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd_fore, ctypes.byref(pid))
            try:
                process = psutil.Process(pid.value)
                if process.name().lower() != "telegram.exe":
                    continue
            except:
                continue
            try:
                img = capture_window(hwnd_fore)
            except Exception as e:
                if mini_chat_win and mini_chat_win.winfo_exists():
                    append_mini_chat(f"Mini Chat [ERROR]: Capture window failed: {e}")
                continue
            prev_image = screenshot_images.get(hwnd_fore)
            if prev_image is not None:
                from skimage.metrics import structural_similarity as ssim
                import numpy as np

                img1 = np.array(prev_image.convert("L"))
                img2 = np.array(img.convert("L"))
                if img1.shape != img2.shape:
                    score = 0
                else:
                    score, _ = ssim(img1, img2, full=True)
                if score >= 0.99:
                    continue
            screenshot_images[hwnd_fore] = img
            filename = os.path.join(TEMP_FOLDER, f"{hwnd_fore}_screenshot.png")
            img.save(filename)
            default_message = "New message detected"
            translation, detected = translate_text_via_chatgpt(
                default_message,
                source_lang="auto",
                target_lang=MY_LANG_SELECTION,
                conversation_context="Conversation transcript translation",
            )
            translation_logs[hwnd_fore] = {"translation": translation}
            if mini_chat_win and mini_chat_win.winfo_exists():
                append_mini_chat(translation)
        except Exception:
            time.sleep(3)
            continue


def start_mini_chat_monitor():
    t = threading.Thread(target=mini_chat_monitor, daemon=True)
    t.start()


def mini_chat_inactivity_monitor():
    global mini_chat_paused, mini_chat_last_active_time
    while True:
        time.sleep(60)
        if not mini_chat_paused and time.time() - mini_chat_last_active_time > 600:
            mini_chat_paused = True
            if mini_chat_pause_button:
                mini_chat_pause_button.config(text="Resume")
            append_mini_chat(
                "Mini Chat đã được tạm dừng do không hoạt động trong 10 phút."
            )


def save_config():
    try:
        config_file = os.path.join(os.getcwd(), "config.ini")
        with open(config_file, "w", encoding="utf-8") as f:
            f.write(f"MY_LANG_SELECTION={MY_LANG_SELECTION}\n")
            f.write(f"TARGET_LANG_SELECTION={TARGET_LANG_SELECTION}\n")
            f.write(f"DPI_ENABLED={DPI_ENABLED}\n")
        for hwnd in list(hwnd_target_lang.keys()):
            hwnd_target_lang[hwnd] = TARGET_LANG_SELECTION
        append_mini_chat("Cài đặt ngôn ngữ và DPI đã được lưu.")
    except Exception:
        append_mini_chat("Mini Chat [ERROR]: Lỗi lưu cài đặt config.")


def destroy_mini_chat():
    on_mini_chat_closed()
    global mini_chat_win, mini_chat_on_close_callback
    if mini_chat_win is not None:
        try:
            if mini_chat_on_close_callback:
                mini_chat_on_close_callback()
        except Exception:
            pass
        try:
            mini_chat_win.destroy()
        except Exception:
            pass
        mini_chat_win = None


# ===== Widget MINI CHATGPT =====
import ctypes.wintypes


class WINDOWPLACEMENT(ctypes.Structure):
    _fields_ = [
        ("length", ctypes.c_uint),
        ("flags", ctypes.c_uint),
        ("showCmd", ctypes.c_uint),
        ("ptMinPosition", ctypes.wintypes.POINT),
        ("ptMaxPosition", ctypes.wintypes.POINT),
        ("rcNormalPosition", ctypes.wintypes.RECT),
    ]


def create_mini_chatgpt():
    global mini_chatgpt_win, mini_chatgpt_entry, mini_chatgpt_pause_button
    global target_lang_display_var

    if root is None:
        return

    mini_chatgpt_win = tk.Toplevel(root)
    mini_chatgpt_win.title("Mini ChatGPT")
    mini_chatgpt_win.geometry("300x200")
    mini_chatgpt_win.overrideredirect(True)
    mini_chatgpt_win.attributes("-topmost", True)
    threading.Thread(
        target=lambda: (
            time.sleep(0.5),
            mini_chatgpt_win.attributes("-topmost", False),
        ),
        daemon=True,
    ).start()

    widget_width, widget_height = 400, 40
    root.update_idletasks()
    tele_x = 1
    tele_y = root.winfo_rooty()
    mini_chatgpt_win.geometry(f"{widget_width}x{widget_height}+{tele_x}+{tele_y}")
    mini_chatgpt_win.withdraw()

    frame = tk.Frame(mini_chatgpt_win)
    frame.pack(fill=tk.BOTH, expand=True)
    vocab_widget = VocabWidget(
        frame, vocab_file="mini_chat/vocabs/vocab_all.json", width=290, height=52
    )
    vocab_widget.grid(row=0, column=0, padx=2, pady=2, sticky="nsew")

    mini_chatgpt_entry = tk.Entry(frame)
    mini_chatgpt_entry.grid(row=0, column=1, sticky="we", padx=4, pady=4, ipady=3)
    mini_chatgpt_entry.config(bd=1, relief="solid", font=("Segoe UI", 10))
    mini_chatgpt_entry.bind("<Return>", lambda e: send_mini_chatgpt_message())
    frame.columnconfigure(1, weight=1)

    def on_target_lang_select(chosen_name):
        global TARGET_LANG_SELECTION
        TARGET_LANG_SELECTION = NAME_TO_LANG_CODE[chosen_name]

    target_lang_menu = tk.OptionMenu(
        frame,
        target_lang_display_var,
        *LANG_CODE_TO_NAME.values(),
        command=on_target_lang_select,
    )
    target_lang_menu.grid(row=0, column=2, padx=4, pady=4)
    target_lang_menu.config(font=("Segoe UI", 9), bd=1, relief="solid")
    btn_send = tk.Button(frame, text="Send", command=send_mini_chatgpt_message)
    btn_send.grid(row=0, column=3, padx=4, pady=2)
    btn_send.config(bd=1, relief="solid", font=("Segoe UI", 9), padx=4, pady=2)
    btn_quit = tk.Button(frame, text="x", command=destroy_mini_chatgpt)
    btn_quit.grid(row=0, column=4, padx=4, pady=2)
    btn_quit.config(bd=1, relief="solid", font=("Segoe UI", 9), padx=4, pady=2)
    threading.Thread(target=update_mini_chatgpt_position, daemon=True).start()


def send_mini_chatgpt_message():
    global mini_chatgpt_entry
    if mini_chatgpt_entry is None:
        return
    msg = mini_chatgpt_entry.get().strip()
    if not msg:
        return
    mini_chatgpt_entry.delete(0, tk.END)
    hwnd = get_correct_telegram_hwnd()
    if hwnd is None:
        return
    default_target = TARGET_LANG_SELECTION or "en"
    target_lang = hwnd_target_lang.get(hwnd, default_target)
    translated, _ = translate_text_via_chatgpt(
        msg, source_lang="auto", target_lang=target_lang
    )
    try:
        send_message_to_telegram_input(hwnd, translated)
        mini_chatgpt_entry.focus_force()
    except Exception:
        pass


def destroy_mini_chatgpt():
    global mini_chatgpt_win, widget_mini_chat_thread_running
    destroy_mini_chat()
    widget_mini_chat_thread_running = False
    if mini_chatgpt_win is not None:
        mini_chatgpt_win.destroy()
        mini_chatgpt_win = None


def update_mini_chatgpt_position():
    global mini_chatgpt_win, widget_mini_chat_thread_running
    while mini_chatgpt_win is not None and widget_mini_chat_thread_running:
        mini_chatgpt_win.update_idletasks()
        hwnd = get_correct_telegram_hwnd()
        if hwnd and not user32.IsIconic(hwnd):
            mini_chatgpt_win.deiconify()
            placement = WINDOWPLACEMENT()
            placement.length = ctypes.sizeof(WINDOWPLACEMENT)
            user32.GetWindowPlacement(hwnd, ctypes.byref(placement))
            if placement.showCmd != 1:
                rect = placement.rcNormalPosition
            else:
                rect = ctypes.wintypes.RECT()
                user32.GetWindowRect(hwnd, ctypes.byref(rect))
            window_width = rect.right - rect.left
            widget_width = window_width
            widget_height = 52
            x = rect.left
            y = rect.bottom + 1
            mini_chatgpt_win.geometry(f"{widget_width}x{widget_height}+{x}+{y}")
            mini_chatgpt_win.lift()
        else:
            mini_chatgpt_win.withdraw()
        time.sleep(0.5)


def toggle_mini_chat_zoom():
    global mini_chat_win
    if mini_chat_win is None:
        create_mini_chat()
    else:
        state = mini_chat_win.state()
        if state in ("withdrawn", "iconic"):
            mini_chat_win.deiconify()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    width = 530
    height = 350
    x = screen_width - width - 50
    y = screen_height - height - 50
    mini_chat_win.geometry(f"{width}x{height}+{x}+{y}")


telegram_window_hwnd = None
mini_chat_visible = False


def track_telegram_window():
    global mini_chat_win, last_valid_telegram_hwnd
    while True:
        try:
            if (
                last_valid_telegram_hwnd
                and mini_chat_win is not None
                and mini_chat_win.winfo_exists()
            ):
                is_visible = user32.IsWindowVisible(last_valid_telegram_hwnd)
                if is_visible:
                    mini_chat_win.deiconify()
                else:
                    mini_chat_win.withdraw()
        except Exception:
            break
        time.sleep(0.5)


def show_mini_chat():
    global mini_chat_win, mini_chatgpt_win
    if mini_chat_win is None:
        create_mini_chat()
    else:
        mini_chat_win.deiconify()
    if mini_chatgpt_win is None:
        create_mini_chatgpt()
    else:
        mini_chatgpt_win.deiconify()


def hide_mini_chat():
    global mini_chat_win, mini_chatgpt_win
    if mini_chat_win is not None:
        mini_chat_win.withdraw()
    if mini_chatgpt_win is not None:
        mini_chatgpt_win.withdraw()


def update_mini_chat_position(telegram_hwnd):
    try:
        if not mini_chat_win or not mini_chat_win.winfo_exists():
            return
        mini_chat_win.attributes("-topmost", True)

        def disable_topmost():
            time.sleep(0.1)
            if mini_chat_win and mini_chat_win.winfo_exists():
                mini_chat_win.attributes("-topmost", False)

        threading.Thread(target=disable_topmost, daemon=True).start()
    except Exception:
        pass
