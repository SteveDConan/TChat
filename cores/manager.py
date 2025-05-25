"""
telegram/manager.py

Chứa các hàm tiện ích quản lý thư mục tài khoản Telegram dạng portable (tdata):
- Lấy danh sách folder tài khoản
- Sao chép telegram.exe hàng loạt
- Xóa session tài khoản
- Thống kê, cập nhật trạng thái
- Các thao tác file/folder hỗ trợ khác

Không chứa code giao diện!
"""

import os
import shutil

# ===============================
# 1. Lấy danh sách các folder tài khoản tdata
# ===============================
def get_tdata_folders(root_folder):
    """
    Quét thư mục gốc, trả về danh sách các thư mục tài khoản chứa 'tdata'.

    Args:
        root_folder (str): Đường dẫn thư mục gốc chứa nhiều tài khoản

    Returns:
        List[str]: Danh sách đường dẫn đến các folder tài khoản hợp lệ
    """
    result = []
    if not os.path.isdir(root_folder):
        return result
    for item in os.listdir(root_folder):
        sub = os.path.join(root_folder, item)
        if os.path.isdir(sub):
            tdata_path = os.path.join(sub, 'tdata')
            if os.path.isdir(tdata_path):
                result.append(sub)
    return result

# ===============================
# 2. Sao chép telegram.exe vào từng folder tài khoản (copy portable)
# ===============================
def copy_telegram_portable(tdata_folders, source_exe):
    """
    Sao chép telegram.exe từ nguồn vào từng folder tài khoản (nếu chưa có).

    Args:
        tdata_folders (List[str]): Danh sách đường dẫn các folder tài khoản
        source_exe (str): Đường dẫn đến telegram.exe nguồn

    Returns:
        dict: Kết quả, ví dụ {'copied': [...], 'skipped': [...], 'errors': [...]}
    """
    copied = []
    skipped = []
    errors = []

    if not os.path.isfile(source_exe):
        return {'copied': [], 'skipped': [], 'errors': ['Source telegram.exe not found!']}

    for folder in tdata_folders:
        target = os.path.join(folder, "telegram.exe")
        if not os.path.isfile(target):
            try:
                shutil.copy(source_exe, target)
                copied.append(folder)
            except Exception as e:
                errors.append(f"{folder}: {e}")
        else:
            skipped.append(folder)
    return {'copied': copied, 'skipped': skipped, 'errors': errors}

# ===============================
# 3. Xóa session của một hoặc nhiều tài khoản
# ===============================
def cleanup_all_sessions(tdata_folders):
    """
    Xóa session file (.session) và folder 'session' bên trong mỗi tài khoản.

    Args:
        tdata_folders (List[str]): Danh sách folder tài khoản

    Returns:
        dict: {'deleted': [...], 'errors': [...]}
    """
    deleted = []
    errors = []
    for folder in tdata_folders:
        session_file = os.path.join(folder, "session.session")
        session_folder = os.path.join(folder, "session")
        # Xóa file .session
        if os.path.isfile(session_file):
            try:
                os.remove(session_file)
                deleted.append(session_file)
            except Exception as e:
                errors.append(f"{session_file}: {e}")
        # Xóa folder session
        if os.path.isdir(session_folder):
            try:
                shutil.rmtree(session_folder)
                deleted.append(session_folder)
            except Exception as e:
                errors.append(f"{session_folder}: {e}")
    return {'deleted': deleted, 'errors': errors}

# ===============================
# 4. Thống kê nhanh số lượng folder hợp lệ
# ===============================
def count_valid_tdata(root_folder):
    """
    Đếm số folder tài khoản hợp lệ (có chứa 'tdata') trong thư mục gốc.

    Args:
        root_folder (str): Đường dẫn thư mục gốc

    Returns:
        int: Số folder tài khoản hợp lệ
    """
    return len(get_tdata_folders(root_folder))

# ===============================
# 5. Hiển thị trạng thái từng folder (vd: đã login hay chưa, có session file hay không)
# ===============================
def status_report(tdata_folders):
    """
    Kiểm tra trạng thái session từng folder tài khoản.

    Args:
        tdata_folders (List[str]): Danh sách folder tài khoản

    Returns:
        List[dict]: Mỗi phần tử {'folder': ..., 'has_session': True/False}
    """
    report = []
    for folder in tdata_folders:
        session_file = os.path.join(folder, "session.session")
        session_folder = os.path.join(folder, "session")
        has_session = os.path.isfile(session_file) or os.path.isdir(session_folder)
        report.append({'folder': folder, 'has_session': has_session})
    return report

# ===============================
# 6. Hàm hỗ trợ: kiểm tra file/folder tồn tại
# ===============================
def check_folder_exists(folder):
    """
    Kiểm tra folder có tồn tại không.

    Args:
        folder (str): Đường dẫn

    Returns:
        bool
    """
    return os.path.isdir(folder)

def check_file_exists(filepath):
    """
    Kiểm tra file có tồn tại không.

    Args:
        filepath (str): Đường dẫn file

    Returns:
        bool
    """
    return os.path.isfile(filepath)
