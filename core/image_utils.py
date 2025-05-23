import ctypes
from ctypes import wintypes
import math
from PIL import Image, ImageChops

def capture_window(hwnd):
    """Capture a window's content using PrintWindow"""
    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32

    # Get window dimensions
    rect = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    width = rect.right - rect.left
    height = rect.bottom - rect.top

    # Create device contexts and bitmap
    hwindc = user32.GetWindowDC(hwnd)
    srcdc = gdi32.CreateCompatibleDC(hwindc)
    bmp = gdi32.CreateCompatibleBitmap(hwindc, width, height)
    gdi32.SelectObject(srcdc, bmp)

    # Capture window content
    result = user32.PrintWindow(hwnd, srcdc, 2)
    if result != 1:
        print("Consolog [WARNING]: PrintWindow không thành công hoặc chỉ chụp được 1 phần.")

    # Define bitmap header structure
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

    # Setup bitmap info
    bmi = BITMAPINFOHEADER()
    bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.biWidth = width
    bmi.biHeight = -height  # Negative height for top-down bitmap
    bmi.biPlanes = 1
    bmi.biBitCount = 32
    bmi.biCompression = 0

    # Create buffer and get bitmap data
    buffer_len = width * height * 4
    buffer = ctypes.create_string_buffer(buffer_len)
    gdi32.GetDIBits(srcdc, bmp, 0, height, buffer, ctypes.byref(bmi), 0)

    # Convert to PIL Image
    image = Image.frombuffer('RGBA', (width, height), buffer, 'raw', 'BGRA', 0, 1)

    # Cleanup
    gdi32.DeleteObject(bmp)
    gdi32.DeleteDC(srcdc)
    user32.ReleaseDC(hwnd, hwindc)

    return image

def compare_screenshot_with_marker(screenshot, marker_image, threshold=20):
    """Compare a screenshot with a marker image using RMS difference"""
    print("Consolog: So sánh ảnh chụp với marker image...")
    
    # Resize marker if needed
    if screenshot.size != marker_image.size:
        marker_image = marker_image.resize(screenshot.size)
    
    # Calculate difference
    diff = ImageChops.difference(screenshot, marker_image)
    h = diff.histogram()
    
    # Calculate RMS
    sq = (value * ((idx % 256) ** 2) for idx, value in enumerate(h))
    sum_sq = sum(sq)
    rms = math.sqrt(sum_sq / (screenshot.size[0] * screenshot.size[1]))
    
    print(f"Consolog: Giá trị RMS = {rms}")
    return rms < threshold 