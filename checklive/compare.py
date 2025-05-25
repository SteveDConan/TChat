# checklive/compare.py

"""
Module: checklive/compare.py
Mục đích:
    - Chụp screenshot của cửa sổ Telegram dựa vào HWND.
    - So sánh ảnh screenshot với marker để xác định trạng thái tài khoản.
    - Có thể thêm worker cho xử lý hàng loạt hoặc đa luồng.

Yêu cầu:
    - Windows OS (sử dụng ctypes)
    - Pillow (PIL) cho xử lý ảnh

Cách sử dụng:
    from checklive.compare import capture_window, compare_screenshot_with_marker
"""

import ctypes
from ctypes import wintypes
import math
from PIL import Image, ImageChops

# === Hàm chụp ảnh cửa sổ Windows theo HWND ===
def capture_window(hwnd):
    """
    Chụp ảnh nội dung của một cửa sổ Windows dựa vào HWND.

    Args:
        hwnd (int): Handle của cửa sổ Windows muốn chụp.

    Returns:
        PIL.Image hoặc None nếu lỗi.
    """
    # Load thư viện GDI32 và USER32
    gdi32 = ctypes.windll.gdi32
    user32 = ctypes.windll.user32

    # Lấy kích thước cửa sổ
    rect = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    width = rect.right - rect.left
    height = rect.bottom - rect.top

    # Tạo device context và bitmap tương thích
    hwindc = user32.GetWindowDC(hwnd)
    srcdc = gdi32.CreateCompatibleDC(hwindc)
    bmp = gdi32.CreateCompatibleBitmap(hwindc, width, height)
    gdi32.SelectObject(srcdc, bmp)

    # Sử dụng PrintWindow để chụp nội dung cửa sổ
    result = user32.PrintWindow(hwnd, srcdc, 2)
    if result != 1:
        print("[WARNING] PrintWindow không thành công hoặc chỉ chụp được một phần cửa sổ.")
        # Không trả về None để vẫn lấy được ảnh, phòng trường hợp vẫn chụp được

    # Chuẩn bị cấu trúc BITMAPINFOHEADER để chuyển về mảng byte
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
    bmi.biHeight = -height  # Để ảnh không bị lật ngược
    bmi.biPlanes = 1
    bmi.biBitCount = 32
    bmi.biCompression = 0

    buffer_len = width * height * 4
    buffer = ctypes.create_string_buffer(buffer_len)

    gdi32.GetDIBits(srcdc, bmp, 0, height, buffer, ctypes.byref(bmi), 0)

    # Tạo ảnh từ buffer byte
    try:
        image = Image.frombuffer('RGBA', (width, height), buffer, 'raw', 'BGRA', 0, 1)
    except Exception as e:
        print(f"[ERROR] Không thể tạo ảnh từ buffer: {e}")
        image = None

    # Giải phóng tài nguyên
    gdi32.DeleteObject(bmp)
    gdi32.DeleteDC(srcdc)
    user32.ReleaseDC(hwnd, hwindc)

    return image

# === Hàm so sánh ảnh screenshot với marker image ===
def compare_screenshot_with_marker(screenshot, marker_image, threshold=20):
    """
    So sánh 2 ảnh (screenshot và marker) bằng chỉ số RMS.

    Args:
        screenshot (PIL.Image): Ảnh screenshot chụp từ cửa sổ Telegram.
        marker_image (PIL.Image): Ảnh marker mẫu (để nhận diện tài khoản chết).
        threshold (float): Ngưỡng RMS. Nhỏ hơn ngưỡng là "giống", lớn hơn là "khác".

    Returns:
        bool: True nếu "giống" marker (có thể coi là chết), False nếu "khác" marker.
    """
    # Resize marker nếu không khớp kích thước
    if screenshot.size != marker_image.size:
        marker_image = marker_image.resize(screenshot.size)

    # Lấy phần khác biệt giữa 2 ảnh
    diff = ImageChops.difference(screenshot, marker_image)
    h = diff.histogram()
    sq = (value * ((idx % 256) ** 2) for idx, value in enumerate(h))
    sum_sq = sum(sq)
    rms = math.sqrt(sum_sq / (screenshot.size[0] * screenshot.size[1]))

    print(f"[INFO] Giá trị RMS so sánh ảnh = {rms}")

    return rms < threshold

# === (OPTIONAL) Worker xử lý hàng loạt (nếu bạn muốn gom các hàm logic worker vào đây) ===
# def screenshot_comparison_worker(...):
#     # Hàm worker: dùng vòng lặp chụp ảnh nhiều cửa sổ, so sánh hàng loạt
#     pass
