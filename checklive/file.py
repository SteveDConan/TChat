# checklive/file.py
"""
Module: checklive.file
Chức năng: Đọc/ghi trạng thái check live (check + live) cho các TData từ file (check_live_status.txt).

Sử dụng để load trạng thái cũ trước khi kiểm tra mới và lưu lại kết quả sau khi kiểm tra.
"""

import os

def load_check_live_status_file(filepath, lang):
    """
    Đọc trạng thái check live từ file lưu trữ (vd: check_live_status.txt).
    Trả về dict có cấu trúc: { tdata_name: {'check': str, 'live': str}, ... }

    - filepath: đường dẫn file trạng thái (ví dụ: "check_live_status.txt")
    - lang: dict language hiện tại (cần để gán mặc định nếu thiếu)

    Trường hợp file không tồn tại sẽ trả về dict rỗng.
    """
    check_live_status = {}
    if not os.path.exists(filepath):
        return check_live_status
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if ": Check:" in line and "| Live:" in line:
                    name_part, rest = line.split(": Check:", 1)
                    tdata_name = name_part.strip()
                    check_part, live_part = rest.split("| Live:", 1)
                    check_live_status[tdata_name] = {
                        "check": check_part.strip() or lang.get("not_checked", ""),
                        "live": live_part.strip() or lang.get("not_checked", ""),
                    }
    except Exception as e:
        print(f"[checklive.file] ERROR reading {filepath}: {e}")
    return check_live_status

def save_check_live_status_file(filepath, check_live_status):
    """
    Ghi trạng thái check live của các TData ra file (vd: check_live_status.txt).
    - filepath: đường dẫn file
    - check_live_status: dict { tdata_name: {'check': str, 'live': str}, ... }
    """
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            for key, val in check_live_status.items():
                line = f"{key}: Check: {val.get('check','')} | Live: {val.get('live','')}\n"
                f.write(line)
    except Exception as e:
        print(f"[checklive.file] ERROR writing {filepath}: {e}")

# === Hướng dẫn sử dụng ===
# Trong app.py hoặc module khác, bạn chỉ cần import và dùng như sau:
# 
# from checklive.file import load_check_live_status_file, save_check_live_status_file
#
# Đọc trạng thái:
#    check_live_status = load_check_live_status_file("check_live_status.txt", lang)
#
# Ghi trạng thái:
#    save_check_live_status_file("check_live_status.txt", check_live_status)
#
# check_live_status là dict có cấu trúc:
#    {
#        'account1': {'check': 'Đã kiểm tra', 'live': 'Live'},
#        'account2': {'check': '...', 'live': '...'},
#    }
