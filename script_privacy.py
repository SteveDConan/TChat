#!/usr/bin/env python
import sys
import time
import ctypes
import threading

# ---------------------------
# Cấu hình Windows Input sử dụng ctypes
from ctypes import wintypes

if not hasattr(wintypes, 'ULONG_PTR'):
    if sys.maxsize > 2**32:
        wintypes.ULONG_PTR = ctypes.c_ulonglong
    else:
        wintypes.ULONG_PTR = ctypes.c_ulong

input_lock = threading.Lock()
SendInput = ctypes.windll.user32.SendInput

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", wintypes.ULONG_PTR)
    ]

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", wintypes.ULONG_PTR)
    ]

class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = [("mi", MOUSEINPUT),
                    ("ki", KEYBDINPUT)]
    _anonymous_ = ("_input",)
    _fields_ = [
        ("type", wintypes.DWORD),
        ("_input", _INPUT)
    ]

def click(x, y):
    """Thực hiện thao tác click chuột tại tọa độ màn hình tuyệt đối."""
    if x < 0 or y < 0:
        print(f"Tọa độ không hợp lệ: ({x}, {y})")
        return
    inp = INPUT(type=0)
    # Sử dụng MOUSEEVENTF_LEFTDOWN (0x0002) và MOUSEEVENTF_LEFTUP (0x0004)
    inp.mi = MOUSEINPUT(dx=x, dy=y, mouseData=0, dwFlags=0x0002 | 0x0004, time=0, dwExtraInfo=0)
    with input_lock:
        SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))

def press_key(vk):
    """Nhấn phím theo mã virtual key."""
    inp = INPUT(type=1)
    inp.ki = KEYBDINPUT(wVk=vk, wScan=0, dwFlags=0, time=0, dwExtraInfo=0)
    with input_lock:
        SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))

def release_key(vk):
    """Nhả phím theo mã virtual key."""
    inp = INPUT(type=1)
    inp.ki = KEYBDINPUT(wVk=vk, wScan=0, dwFlags=0x0002, time=0, dwExtraInfo=0)
    with input_lock:
        SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))

# ---------------------------
# Cấu hình VirtualInput dùng PostMessage (nếu win32 có sẵn)
try:
    import win32gui
    import win32con
except ImportError:
    win32gui = None
    win32con = None

class VirtualInput:
    def __init__(self, hwnd):
        self.hwnd = hwnd
        print(f"[VirtualInput] Khởi tạo cho cửa sổ có handle: {self.hwnd}")

    def send_key(self, vk_code):
        """Gửi phím đến cửa sổ bằng PostMessage nếu có, ngược lại dùng SendInput."""
        print(f"[VirtualInput] Gửi phím (vk: {vk_code}) tới cửa sổ {self.hwnd}")
        if win32gui and win32con and self.hwnd:
            win32gui.PostMessage(self.hwnd, win32con.WM_KEYDOWN, vk_code, 0)
            time.sleep(0.2)
            win32gui.PostMessage(self.hwnd, win32con.WM_KEYUP, vk_code, 0)
        else:
            press_key(vk_code)
            time.sleep(0.2)
            release_key(vk_code)

    def mouse_click(self, x, y):
        """Thực hiện thao tác click chuột tại tọa độ cho cửa sổ mục tiêu."""
        print(f"[VirtualInput] Click tại ({x}, {y}) cho cửa sổ {self.hwnd}")
        if win32gui and win32con and self.hwnd:
            lParam = (y << 16) | (x & 0xFFFF)
            win32gui.PostMessage(self.hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
            time.sleep(0.2)
            win32gui.PostMessage(self.hwnd, win32con.WM_LBUTTONUP, 0, lParam)
        else:
            click(x, y)
            time.sleep(0.2)

# ---------------------------
# Các hàm thao tác quyền riêng tư trên cửa sổ có kích thước 500×504
def hide_phone_number(vi):
    """
    Thực hiện thao tác ẩn số điện thoại.
    Điều chỉnh tọa độ (x, y) dựa trên cửa sổ kích thước 500×504.
    Ví dụ: nếu nút Ẩn số nằm ở vị trí (150, 300) so với góc trên bên trái của cửa sổ.
    """
    x, y = 150, 300
    print("[Privacy] Thực hiện thao tác ẩn số điện thoại tại vị trí:", (x, y))
    vi.mouse_click(x, y)
    time.sleep(0.5)

def block_unknown_calls(vi):
    """
    Thực hiện thao tác chặn cuộc gọi từ người lạ.
    Điều chỉnh tọa độ (x, y) dựa trên cửa sổ kích thước 500×504.
    Ví dụ: nếu nút Chặn cuộc gọi nằm ở vị trí (150, 350) so với góc trên bên trái của cửa sổ.
    """
    x, y = 150, 350
    print("[Privacy] Thực hiện thao tác chặn cuộc gọi từ người lạ tại vị trí:", (x, y))
    vi.mouse_click(x, y)
    time.sleep(0.5)

# ---------------------------
# Hàm main: nhận tham số dòng lệnh và thực hiện thao tác thật trên cửa sổ kích thước 500×504
def main():
    """
    Cách chạy:
      python script_privacy.py <tdata_path> <window_handle>
    Nếu không truyền đủ tham số, script sẽ dùng giá trị mặc định.
    Lưu ý: window_handle phải là số nguyên đại diện cho handle của cửa sổ mục tiêu.
    """
    if len(sys.argv) >= 3:
        tdata_path = sys.argv[1]
        try:
            hwnd = int(sys.argv[2])
        except ValueError:
            print("Lỗi: window_handle phải là số nguyên.")
            return
    else:
        tdata_path = "default_tdata"
        hwnd = None

    print(f"[Privacy] Cập nhật quyền riêng tư cho Tdata tại '{tdata_path}' với handle: {hwnd}")
    
    # Nếu có handle, tạo đối tượng VirtualInput
    if hwnd:
        vi = VirtualInput(hwnd)
    else:
        print("[Privacy] Không tìm thấy handle cửa sổ, sử dụng thao tác SendInput trực tiếp.")
        # Sử dụng đối tượng Dummy để gọi hàm click
        class DummyVI:
            def mouse_click(self, x, y):
                click(x, y)
        vi = DummyVI()

    # Thực hiện thao tác trên cửa sổ đã được điều chỉnh kích thước 500×504
    hide_phone_number(vi)
    block_unknown_calls(vi)

    print("[Privacy] Quyền riêng tư đã được cập nhật thành công trên cửa sổ kích thước 500×504!")

if __name__ == '__main__':
    main()



