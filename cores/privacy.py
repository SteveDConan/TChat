# telegram/privacy.py

"""
Module quản lý quyền riêng tư cho các tài khoản Telegram.
Dùng Telethon để cập nhật các setting về hiển thị số điện thoại, cuộc gọi v.v.
"""

import asyncio
from telethon.sync import TelegramClient
from telethon import functions, types
from resources.config import API_ID, API_HASH
from resources.utils import log_message

def update_privacy_sync(session_path):
    """
    Hàm đồng bộ: Cập nhật quyền riêng tư cho một session Telegram.

    session_path: Đường dẫn tới file hoặc folder session của account Telegram.
    """
    asyncio.run(update_privacy(session_path))


async def update_privacy(session_path):
    """
    Hàm bất đồng bộ: Cập nhật quyền riêng tư cho account Telegram.

    - Ẩn số điện thoại (không ai xem được).
    - Ẩn cuộc gọi (không ai gọi được).

    Args:
        session_path (str): Đường dẫn tới session file/folder Telegram.

    Returns:
        None
    """
    print(f"[privacy] Cập nhật quyền riêng tư cho session: {session_path}")
    client = TelegramClient(session_path, API_ID, API_HASH)
    try:
        await client.connect()
    except Exception as e:
        log_message(f"[privacy][ERROR]: Lỗi kết nối tới Telegram: {e}")
        return

    try:
        # Đặt quyền riêng tư: Không ai xem số điện thoại
        await client(functions.account.SetPrivacyRequest(
            key=types.InputPrivacyKeyPhoneNumber(),
            rules=[types.InputPrivacyValueDisallowAll()]
        ))

        # Đặt quyền riêng tư: Không ai gọi đến (nếu Telethon support)
        if hasattr(types, "InputPrivacyKeyCalls"):
            await client(functions.account.SetPrivacyRequest(
                key=types.InputPrivacyKeyCalls(),
                rules=[types.InputPrivacyValueDisallowAll()]
            ))
            log_message(f"[privacy] Đã ẩn cuộc gọi cho session {session_path}")
        else:
            log_message("[privacy] Telethon không hỗ trợ InputPrivacyKeyCalls, bỏ qua.")

        log_message(f"[privacy] Đã cập nhật quyền riêng tư thành công cho session {session_path}")
    except Exception as e:
        log_message(f"[privacy][ERROR]: Lỗi cập nhật quyền riêng tư: {e}")
    finally:
        await client.disconnect()


def run_update_privacy_multi(session_paths):
    """
    Cập nhật quyền riêng tư cho nhiều session Telegram.

    Args:
        session_paths (list): Danh sách đường dẫn tới session file/folder.

    Returns:
        None
    """
    for session_path in session_paths:
        update_privacy_sync(session_path)

