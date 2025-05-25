"""
telegram/session.py

Module này quản lý toàn bộ các hàm liên quan đến session Telegram:
- Đăng nhập bằng Telethon
- Xử lý OTP và 2FA
- Kiểm tra đã ủy quyền chưa
- Cleanup/xóa session
- Parse password từ file
"""

import os
import asyncio
import shutil
import threading

from telethon.sync import TelegramClient
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, PhoneCodeExpiredError

# Nếu cần: import các biến config dùng chung
from resources.config import API_ID, API_HASH
from resources.utils import log_message

# ==========================
# 1. Kiểm tra đã ủy quyền chưa (asynchronous)
# ==========================
async def check_authorization(session_path, phone):
    """
    Kiểm tra xem session Telegram đã được ủy quyền chưa.
    Dùng cho bước login và kiểm tra lại session cũ.

    Args:
        session_path (str): Đường dẫn tới file session hoặc thư mục session.
        phone (str): Số điện thoại Telegram (hiển thị log).

    Returns:
        bool: True nếu đã ủy quyền, False nếu chưa.
    """
    print(f"[Session] Kiểm tra authorization cho {phone} (session: {session_path})")
    client = TelegramClient(session_path, API_ID, API_HASH)
    try:
        await client.connect()
        authorized = await client.is_user_authorized()
        await client.disconnect()
        return authorized
    except Exception as e:
        print(f"[Session][ERROR]: Lỗi kiểm tra authorization cho {phone}: {e}")
        return False

# ==========================
# 2. Hàm dọn dẹp session (cleanup)
# ==========================
def cleanup_session_files(session_base):
    """
    Xóa file session (.session) và thư mục session nếu có, dùng khi đăng nhập lỗi hoặc cần reset.

    Args:
        session_base (str): Đường dẫn session không có đuôi (vd: 'folder/session')
    """
    session_file = session_base + ".session"
    if os.path.exists(session_file):
        try:
            os.remove(session_file)
            print(f"[Session] Đã xóa file session {session_file}")
        except Exception as e:
            print(f"[Session][ERROR]: Lỗi xóa file session {session_file}: {e}")
    if os.path.exists(session_base) and os.path.isdir(session_base):
        try:
            shutil.rmtree(session_base)
            print(f"[Session] Đã xóa thư mục session {session_base}")
        except Exception as e:
            print(f"[Session][ERROR]: Lỗi xóa thư mục {session_base}: {e}")

# ==========================
# 3. Hàm parse mật khẩu 2FA từ file tdata
# ==========================
def parse_2fa_info(tdata_folder):
    """
    Tìm và đọc mật khẩu 2FA trong các file text trong thư mục tdata.

    Args:
        tdata_folder (str): Đường dẫn thư mục tdata (chứa các file .txt hoặc '2fa')

    Returns:
        dict: {'password': 'xxx'} nếu tìm thấy, ngược lại trả về {}
    """
    for root_dir, dirs, files in os.walk(tdata_folder):
        for file in files:
            if file.lower().endswith('.txt') and "2fa" in file.lower():
                path = os.path.join(root_dir, file)
                try:
                    with open(path, "r", encoding="utf-8-sig") as f:
                        lines = [line.strip() for line in f if line.strip()]
                    if len(lines) == 1:
                        return {"password": lines[0]}
                except Exception as e:
                    print(f"[Session][ERROR]: Lỗi đọc file {path}: {e}")
    # Nếu không tìm thấy file 2fa, thử tìm file .txt khác có 1 dòng
    for root_dir, dirs, files in os.walk(tdata_folder):
        for file in files:
            if file.lower().endswith('.txt') and "2fa" not in file.lower():
                path = os.path.join(root_dir, file)
                try:
                    with open(path, "r", encoding="utf-8-sig") as f:
                        lines = [line.strip() for line in f if line.strip()]
                    if len(lines) == 1:
                        return {"password": lines[0]}
                except Exception as e:
                    print(f"[Session][ERROR]: Lỗi đọc file {path}: {e}")
    return {}

# ==========================
# 4. Hàm nhập OTP từ UI (nên truyền callback hoặc dùng tkinter ngoài)
# ==========================
def get_otp(phone, lang, root):
    """
    Yêu cầu người dùng nhập OTP từ UI (tkinter).
    Hàm này cần truyền lang (dict ngôn ngữ) và root (Tk window).

    Args:
        phone (str): Số điện thoại Telegram
        lang (dict): Biến ngôn ngữ (cho message)
        root (tk.Tk): Cửa sổ root để gọi dialog

    Returns:
        str: OTP người dùng nhập, hoặc None nếu bỏ qua
    """
    from tkinter import simpledialog
    print(f"[Session] Yêu cầu nhập OTP cho {phone}")
    otp_result = [None]
    event = threading.Event()
    def ask():
        otp_result[0] = simpledialog.askstring("OTP", lang["otp_prompt"].format(phone=phone), parent=root)
        event.set()
    root.after(0, ask)
    event.wait()
    return otp_result[0]

# ==========================
# 5. Hàm đăng nhập bất đồng bộ (async)
# ==========================
async def async_login(session_path, phone, tdata_folder, lang, root):
    """
    Đăng nhập Telegram, xử lý OTP, 2FA, cleanup khi lỗi, lưu session mới.

    Args:
        session_path (str): Đường dẫn session mới.
        phone (str): Số điện thoại Telegram.
        tdata_folder (str): Thư mục tdata chứa session và file 2FA (nếu có).
        lang (dict): Ngôn ngữ hiển thị popup (báo lỗi/thông báo).
        root (tk.Tk): Để show dialog OTP.

    Returns:
        bool: True nếu login thành công, False nếu thất bại.
    """
    client = TelegramClient(session_path, API_ID, API_HASH)
    try:
        await client.connect()
    except Exception as e:
        log_message(f"[Session][ERROR]: Lỗi kết nối cho {phone}: {e}")
        cleanup_session_files(session_path)
        return False

    if not await client.is_user_authorized():
        try:
            await client.send_code_request(phone)
            log_message(f"[Session]: Đã gửi OTP cho {phone}")
        except Exception as e:
            log_message(f"[Session][ERROR]: Gửi mã OTP thất bại cho {phone}: {e}")
            await client.disconnect()
            cleanup_session_files(session_path)
            return False
        otp = get_otp(phone, lang, root)
        if not otp:
            log_message(f"[Session][ERROR]: Không nhập OTP cho {phone}")
            await client.disconnect()
            cleanup_session_files(session_path)
            return False
        try:
            await client.sign_in(phone, otp)
            if not await client.is_user_authorized():
                raise Exception("Đăng nhập OTP không thành công, cần 2FA")
            log_message(f"[Session]: Đăng nhập thành công cho {phone} (không 2FA)")
        except SessionPasswordNeededError:
            twofa_info = parse_2fa_info(tdata_folder)
            if "password" not in twofa_info:
                log_message(f"[Session][ERROR]: Không tìm thấy mật khẩu 2FA cho {phone}")
                await client.disconnect()
                cleanup_session_files(session_path)
                return False
            password_2fa = twofa_info["password"]
            try:
                await client.sign_in(password=password_2fa)
                if not await client.is_user_authorized():
                    raise Exception("Đăng nhập không thành công sau khi nhập mật khẩu 2FA.")
                log_message(f"[Session]: Đăng nhập thành công cho {phone} (2FA)")
            except Exception as e2:
                log_message(f"[Session][ERROR]: Lỗi đăng nhập 2FA cho {phone}: {e2}")
                await client.disconnect()
                cleanup_session_files(session_path)
                return False
        except PhoneCodeInvalidError:
            log_message(f"[Session][ERROR]: Mã OTP không đúng cho {phone}!")
            await client.disconnect()
            cleanup_session_files(session_path)
            return False
        except PhoneCodeExpiredError:
            log_message(f"[Session][ERROR]: Mã OTP đã hết hạn cho {phone}!")
            await client.disconnect()
            cleanup_session_files(session_path)
            return False
        except Exception as e:
            log_message(f"[Session][ERROR]: Đăng nhập thất bại cho {phone}: {e}")
            await client.disconnect()
            cleanup_session_files(session_path)
            return False
    log_message(f"[Session]: Session cho {phone} đã được lưu tại {session_path}")
    await client.disconnect()
    return True

# ==========================
# 6. Hàm login một tài khoản từ UI (sử dụng từ luồng/tkinter)
# ==========================
def login_account(tdata_folder, update_item_callback, lang, root):
    """
    Đăng nhập một tài khoản Telegram bằng session tdata.
    Gọi bất đồng bộ và cập nhật status về UI.

    Args:
        tdata_folder (str): Đường dẫn thư mục tdata của tài khoản
        update_item_callback (callable): Hàm callback cập nhật status lên giao diện
        lang (dict): Biến ngôn ngữ
        root (tk.Tk): Để show dialog OTP

    Returns:
        bool: True nếu đăng nhập thành công, False nếu lỗi
    """
    session_file = os.path.join(tdata_folder, "session.session")
    session_folder = os.path.join(tdata_folder, "session")
    phone = os.path.basename(tdata_folder)
    # Mở Telegram bằng portable trước (nếu cần)
    # (Có thể truyền thêm hàm open_telegram_with_tdata vào nếu muốn tách logic)
    if os.path.exists(session_file) or os.path.exists(session_folder):
        authorized = asyncio.run(check_authorization(session_folder, phone))
        if authorized:
            update_item_callback(phone, lang["skipped"])
            return True
        else:
            cleanup_session_files(session_folder)
    # Đăng nhập mới (có thể truyền thêm biến cho open_telegram_with_tdata nếu muốn)
    result = asyncio.run(async_login(os.path.join(tdata_folder, "session"), phone, tdata_folder, lang, root))
    if result:
        update_item_callback(phone, lang["success"])
    else:
        update_item_callback(phone, lang["failure"])
    return result
