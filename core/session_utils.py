import os
import shutil
import asyncio
from telethon.sync import TelegramClient
from telethon import functions, types
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, PhoneCodeExpiredError
from tkinter import simpledialog, messagebox

from .config import API_ID, API_HASH
from .language import lang

successful_sessions = set()

def cleanup_session_files(session_base):
    """Clean up session files and folders"""
    session_file = session_base + ".session"
    print(f"Consolog: Đang dọn dẹp session từ: {session_base}")
    if os.path.exists(session_file):
        try:
            os.remove(session_file)
            print(f"Consolog: Đã xóa file session {session_file}")
        except Exception as e:
            print(f"Consolog [ERROR]: Lỗi xóa file session {session_file}: {e}")
    if os.path.exists(session_base) and os.path.isdir(session_base):
        try:
            shutil.rmtree(session_base)
            print(f"Consolog: Đã xóa thư mục session {session_base}")
        except Exception as e:
            print(f"Consolog [ERROR]: Lỗi xóa thư mục {session_base}: {e}")

def parse_2fa_info(tdata_folder):
    """Parse 2FA information from TData folder"""
    print(f"Consolog: Đang parse thông tin 2FA từ folder: {tdata_folder}")
    for root_dir, dirs, files in os.walk(tdata_folder):
        for file in files:
            if file.lower().endswith('.txt') and "2fa" in file.lower():
                path = os.path.join(root_dir, file)
                print(f"Consolog: Kiểm tra candidate 2FA file: {path}")
                try:
                    with open(path, "r", encoding="utf-8-sig") as f:
                        lines = [line.strip() for line in f if line.strip()]
                    if len(lines) == 1:
                        print(f"Consolog: Tìm thấy mật khẩu 2FA: {lines[0]}")
                        return {"password": lines[0]}
                except Exception as e:
                    print(f"Consolog [ERROR]: Lỗi đọc file {path}: {e}")
    return {}

def get_otp(phone, root):
    """Get OTP code from user input"""
    print(f"Consolog: Yêu cầu nhập OTP cho {phone}")
    otp_result = [None]
    event = asyncio.Event()
    
    def ask():
        otp_result[0] = simpledialog.askstring("OTP", lang["otp_prompt"].format(phone=phone), parent=root)
        print(f"Consolog: OTP đã được nhập: {otp_result[0]}")
        event.set()
    
    root.after(0, ask)
    event.wait()
    return otp_result[0]

async def check_authorization(session_path, phone):
    """Check if a session is authorized"""
    print(f"Consolog: Kiểm tra authorization cho {phone} từ session: {session_path}")
    client = TelegramClient(session_path, API_ID, API_HASH)
    try:
        await client.connect()
        authorized = await client.is_user_authorized()
        await client.disconnect()
        print(f"Consolog: Authorization cho {phone}: {authorized}")
        return authorized
    except Exception as e:
        print(f"Consolog [ERROR]: Lỗi kiểm tra authorization cho {phone}: {e}")
        return False

async def update_privacy(session_path):
    """Update privacy settings for a session"""
    print(f"Consolog: Đang cập nhật quyền riêng tư cho session: {session_path}")
    client = TelegramClient(session_path, API_ID, API_HASH)
    try:
        await client.connect()
        await client(functions.account.SetPrivacyRequest(
            key=types.InputPrivacyKeyPhoneNumber(),
            rules=[types.InputPrivacyValueDisallowAll()]
        ))
        if hasattr(types, "InputPrivacyKeyCalls"):
            await client(functions.account.SetPrivacyRequest(
                key=types.InputPrivacyKeyCalls(),
                rules=[types.InputPrivacyValueDisallowAll()]
            ))
        print(f"Consolog: Cập nhật quyền riêng tư thành công cho session {session_path}")
    except Exception as e:
        print(f"Consolog [ERROR]: Lỗi cập nhật quyền riêng tư cho session {session_path}: {e}")
    finally:
        await client.disconnect()

async def async_login(session_path, phone, tdata_folder, root):
    """Handle the login process for a Telegram account"""
    print(f"Consolog: Bắt đầu đăng nhập cho {phone} với session: {session_path}")
    client = TelegramClient(session_path, API_ID, API_HASH)
    
    try:
        await client.connect()
    except Exception as e:
        print(f"Consolog [ERROR]: Lỗi kết nối cho {phone}: {e}")
        cleanup_session_files(session_path)
        return False

    if not await client.is_user_authorized():
        try:
            await client.send_code_request(phone)
            print(f"Consolog: Đã gửi OTP cho {phone}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Gửi mã OTP thất bại cho {phone}: {e}")
            await client.disconnect()
            cleanup_session_files(session_path)
            return False

        otp = get_otp(phone, root)
        if not otp:
            messagebox.showerror("Lỗi", "Không nhập OTP.")
            await client.disconnect()
            cleanup_session_files(session_path)
            return False

        try:
            await client.sign_in(phone, otp)
            if not await client.is_user_authorized():
                raise Exception("Đăng nhập OTP không thành công, cần 2FA")
            print(f"Consolog: Đăng nhập thành công cho {phone} (không 2FA)")
        except SessionPasswordNeededError:
            twofa_info = parse_2fa_info(tdata_folder)
            if "password" not in twofa_info:
                messagebox.showerror("Lỗi", lang["2fa_error"].format(phone=phone))
                await client.disconnect()
                cleanup_session_files(session_path)
                return False
            
            try:
                await client.sign_in(password=twofa_info["password"])
                if not await client.is_user_authorized():
                    raise Exception("Đăng nhập không thành công sau khi nhập mật khẩu 2FA.")
                print(f"Consolog: Đăng nhập thành công cho {phone} (2FA)")
            except Exception as e2:
                print(f"Consolog [ERROR]: Lỗi đăng nhập 2FA cho {phone}: {e2}")
                messagebox.showerror("Lỗi", f"Đăng nhập 2FA thất bại cho {phone}: {e2}")
                await client.disconnect()
                cleanup_session_files(session_path)
                return False
        except (PhoneCodeInvalidError, PhoneCodeExpiredError) as e:
            error_msg = "Mã OTP không đúng" if isinstance(e, PhoneCodeInvalidError) else "Mã OTP đã hết hạn"
            messagebox.showerror("Lỗi", f"{error_msg} cho {phone}!")
            await client.disconnect()
            cleanup_session_files(session_path)
            return False
        except Exception as e:
            messagebox.showerror("Lỗi", f"Đăng nhập thất bại cho {phone}: {e}")
            await client.disconnect()
            cleanup_session_files(session_path)
            return False

    print(f"Consolog: Session cho {phone} đã được lưu tại {session_path}")
    await client.disconnect()
    return True 