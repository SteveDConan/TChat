import os
import time
import subprocess
import ctypes
from ctypes import wintypes
from tkinter import messagebox
from PIL import Image, ImageChops

from .language import lang
from .image_utils import capture_window

user32 = ctypes.windll.user32

def get_window_handle_by_pid(pid):
    """Get window handle by process ID"""
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
    if handles:
        return handles[0]
    return None

def open_telegram_with_tdata(tdata_folder):
    """Open Telegram with specific TData folder"""
    telegram_exe = os.path.join(tdata_folder, "telegram.exe")
    tdata_sub = os.path.join(tdata_folder, "tdata")
    print(f"Consolog: Mở telegram từ folder: {tdata_folder}")
    
    if not os.path.exists(telegram_exe):
        print(f"Không tìm thấy telegram.exe tại {telegram_exe}")
        return None
    if not os.path.exists(tdata_sub):
        print(f"Không tìm thấy thư mục tdata tại {tdata_sub}")
        return None
    
    print(f"🟢 Đang mở {telegram_exe} (cwd={tdata_folder})")
    proc = subprocess.Popen([telegram_exe], cwd=tdata_folder)
    time.sleep(1)
    return proc

def arrange_telegram_windows(custom_width=500, custom_height=504, for_check_live=False):
    """Arrange Telegram windows in a grid or cascade pattern"""
    print(f"Consolog: Sắp xếp cửa sổ Telegram với kích thước {custom_width}x{custom_height}... For check live: {for_check_live}")
    handles = []
    seen_pids = set()

    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
    def enum_callback(hwnd, lParam):
        if user32.IsWindowVisible(hwnd):
            pid = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            process_name = ""
            try:
                import psutil
                process = psutil.Process(pid.value)
                process_name = process.name()
            except:
                pass
            
            if process_name.lower() == "telegram.exe":
                if for_check_live:
                    handles.append(hwnd)
                    print(f"Consolog: Thêm cửa sổ HWND {hwnd} từ PID {pid.value} (check live mode)")
                else:
                    if pid.value not in seen_pids:
                        seen_pids.add(pid.value)
                        handles.append(hwnd)
                        print(f"Consolog: Thêm cửa sổ HWND {hwnd} từ PID {pid.value}")
        return True

    user32.EnumWindows(enum_callback, 0)
    n = len(handles)
    print(f"Consolog: Tìm thấy {n} cửa sổ Telegram.")
    
    if n == 0:
        messagebox.showinfo("Arrange", "Không tìm thấy cửa sổ Telegram nào.")
        return

    screen_width = user32.GetSystemMetrics(0)
    screen_height = user32.GetSystemMetrics(1)
    max_cols = screen_width // custom_width
    max_rows = screen_height // custom_height
    
    if max_cols < 1: max_cols = 1
    if max_rows < 1: max_rows = 1
    
    capacity = max_cols * max_rows
    SWP_NOZORDER = 0x0004
    SWP_SHOWWINDOW = 0x0040

    if n <= capacity:
        for index, hwnd in enumerate(handles):
            row = index // max_cols
            col = index % max_cols
            x = col * custom_width
            y = row * custom_height
            user32.SetWindowPos(hwnd, None, x, y, custom_width, custom_height, SWP_NOZORDER | SWP_SHOWWINDOW)
            user32.RedrawWindow(hwnd, None, None, 0x1 | 0x100 | 0x80)
            time.sleep(0.1)
            print(f"Consolog: Di chuyển cửa sổ HWND {hwnd} đến vị trí ({x}, {y})")
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
                
            user32.SetWindowPos(hwnd, None, x, y, custom_width, custom_height, SWP_NOZORDER | SWP_SHOWWINDOW)
            user32.RedrawWindow(hwnd, None, None, 0x1 | 0x100 | 0x80)
            time.sleep(0.1)
            print(f"Consolog: (Cascade) Di chuyển cửa sổ HWND {hwnd} đến vị trí ({x}, {y})")

    messagebox.showinfo("Arrange", lang["arrange_result"].format(count=n))

def close_all_telegram():
    """Close all running Telegram instances"""
    print("Consolog: Đang đóng tất cả tiến trình Telegram...")
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq Telegram.exe", "/FO", "CSV"],
            capture_output=True, text=True
        )
        output = result.stdout.strip().splitlines()
        pids = []
        closed = []
        errors = []
        
        for line in output[1:]:
            parts = line.replace('"','').split(',')
            if len(parts) >= 2:
                pids.append(parts[1])
        
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
        print(summary)
        messagebox.showinfo(lang["close_result_title"], summary)
        print("Consolog: Đóng tiến trình Telegram hoàn tất.")
        return True
    except Exception as e:
        messagebox.showerror("Lỗi", f"Không thể đóng các tiến trình Telegram: {e}")
        return False

# ✅ BỔ SUNG: open_telegram_window cho check_live_ui dùng
def open_telegram_window(telegram_path, account_folder):
    """Mở Telegram và trả lại handle cửa sổ"""
    tdata_path = os.path.join(account_folder, "tdata")

    if not os.path.exists(telegram_path):
        print(f"Không tìm thấy Telegram.exe tại {telegram_path}")
        return None

    if not os.path.exists(tdata_path):
        print(f"Không tìm thấy thư mục tdata tại {tdata_path}")
        return None

    print(f"Consolog: Mở Telegram tại {telegram_path} với tdata tại {tdata_path}")
    proc = subprocess.Popen([telegram_path], cwd=account_folder)
    time.sleep(1)

    hwnd = get_window_handle_by_pid(proc.pid)
    return hwnd

def close_telegram_window(hwnd):
    """Close the specific Telegram window using its HWND."""
    try:
        user32.PostMessageW(hwnd, 0x10, 0, 0)  # Send WM_CLOSE message to close the window
        print(f"Consolog: Đang đóng cửa sổ Telegram với HWND {hwnd}")
    except Exception as e:
        print(f"Consolog: Không thể đóng cửa sổ Telegram với HWND {hwnd}: {e}")

# Định nghĩa hàm so sánh ảnh
def compare_images_with_marker(image_path, marker_path):
    """So sánh hai ảnh và kiểm tra nếu chúng khớp với ảnh marker"""
    try:
        # Mở ảnh
        image = Image.open(image_path)
        marker = Image.open(marker_path)

        # So sánh ảnh
        diff = ImageChops.difference(image, marker)
        if diff.getbbox():
            print("Ảnh không khớp.")
            return False
        else:
            print("Ảnh khớp.")
            return True
    except Exception as e:
        print(f"Lỗi khi so sánh ảnh: {e}")
        return False
