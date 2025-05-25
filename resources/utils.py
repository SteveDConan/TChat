# resources/utils.py
# Các hàm tiện ích dùng chung cho toàn bộ dự án (đọc/ghi file, thao tác UI, log, clipboard...)

import os
import json

# =========================
# 1. Hàm đọc/ghi file text
# =========================

def read_file(filepath, default=None, encoding="utf-8"):
    """
    Đọc toàn bộ nội dung file text.
    Trả về nội dung file dưới dạng chuỗi, nếu không tồn tại thì trả về default.
    """
    if not os.path.exists(filepath):
        return default
    with open(filepath, "r", encoding=encoding) as f:
        return f.read().strip()

def write_file(filepath, content, encoding="utf-8"):
    """
    Ghi một chuỗi nội dung vào file, ghi đè lên file cũ.
    """
    with open(filepath, "w", encoding=encoding) as f:
        f.write(content)

# =========================
# 2. Hàm đọc/ghi file JSON
# =========================

def read_json(filepath, default=None, encoding="utf-8"):
    """
    Đọc file JSON, trả về dict (hoặc list).
    Nếu lỗi hoặc không tồn tại file thì trả về default.
    """
    if not os.path.exists(filepath):
        return default
    with open(filepath, "r", encoding=encoding) as f:
        try:
            return json.load(f)
        except Exception as e:
            print(f"[utils] Lỗi đọc JSON {filepath}: {e}")
            return default

def write_json(filepath, data, encoding="utf-8"):
    """
    Ghi dict hoặc list thành file JSON, định dạng dễ đọc (indent=2).
    """
    with open(filepath, "w", encoding=encoding) as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# =========================
# 3. Hàm xử lý giao diện (Tkinter)
# =========================

def center_window(win, width, height):
    """
    Đưa cửa sổ Tkinter ra giữa màn hình.
    win: đối tượng cửa sổ (Tk hoặc Toplevel)
    width, height: kích thước cửa sổ mong muốn
    """
    win.update_idletasks()
    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    win.geometry(f"{width}x{height}+{x}+{y}")

def copy_to_clipboard(root, text):
    """
    Copy text vào clipboard của hệ điều hành.
    root: Tk hoặc Toplevel hiện tại (nên truyền vào)
    text: chuỗi cần copy
    """
    root.clipboard_clear()
    root.clipboard_append(text)
    root.update()  # Đảm bảo clipboard lưu dữ liệu

# =========================
# 4. Hàm thao tác với thư mục TData
# =========================

def get_tdata_folders(main_dir):
    """
    Lấy danh sách đường dẫn tất cả thư mục con trong main_dir (thường là các folder TData).
    Chỉ trả về folder, không trả về file.
    """
    if not os.path.exists(main_dir):
        return []
    return [
        os.path.join(main_dir, f) for f in os.listdir(main_dir)
        if os.path.isdir(os.path.join(main_dir, f))
    ]

# =========================
# 5. Hàm log ra Text widget Tkinter
# =========================

def log_message(text_widget, msg):
    """
    Ghi một dòng log vào widget Text (Tkinter), đồng thời in ra terminal.
    text_widget: widget kiểu Text
    msg: nội dung log
    """
    text_widget.insert("end", msg + "\n")
    text_widget.see("end")
    print("[LOG]", msg)

# =========================
# 6. Hàm đọc/ghi kích thước cửa sổ
# =========================

def load_window_size(filepath, default_width=500, default_height=504):
    """
    Đọc kích thước cửa sổ (width, height) từ file dạng "width,height".
    Nếu lỗi hoặc file không tồn tại thì trả về giá trị mặc định.
    """
    if os.path.exists(filepath):
        try:
            with open(filepath, "r") as f:
                line = f.read().strip()
                parts = line.split(",")
                if len(parts) == 2:
                    width = int(parts[0])
                    height = int(parts[1])
                    return width, height
        except Exception as e:
            print(f"[utils] Lỗi load kích thước cửa sổ: {e}")
    return default_width, default_height

def save_window_size(filepath, width, height):
    """
    Ghi kích thước cửa sổ ra file theo định dạng "width,height".
    """
    try:
        with open(filepath, "w") as f:
            f.write(f"{width},{height}")
    except Exception as e:
        print(f"[utils] Lỗi lưu kích thước cửa sổ: {e}")

# =========================
# 7. Hàm đọc/ghi API key (ví dụ dùng cho ChatGPT)
# =========================

def load_chatgpt_api_key(filepath):
    """
    Đọc API key ChatGPT từ file.
    """
    return read_file(filepath, default="")

def save_chatgpt_api_key(filepath, key):
    """
    Ghi API key ChatGPT vào file.
    """
    write_file(filepath, key)
