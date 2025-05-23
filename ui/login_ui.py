import os
import asyncio
import tkinter as tk
from tkinter import ttk, messagebox
from telethon.sync import TelegramClient
from telethon.errors import (
    PhoneNumberInvalidError, ApiIdInvalidError,
    PhoneCodeInvalidError, SessionPasswordNeededError
)

from core.config import API_ID, API_HASH
from core.session_utils import cleanup_session_files
from core.language import lang

def login_all_accounts(root, entry_path):
    """Login to all Telegram accounts in the specified directory"""
    tdata_dir = entry_path.get()
    if not os.path.exists(tdata_dir):
        messagebox.showerror("Lỗi", lang["msg_error_path"])
        return

    folders = [
        os.path.join(tdata_dir, f) for f in os.listdir(tdata_dir)
        if os.path.isdir(os.path.join(tdata_dir, f))
    ]

    if not folders:
        messagebox.showerror("Lỗi", lang["msg_no_folders"])
        return

    # Create login window
    login_window = tk.Toplevel(root)
    login_window.title(lang["login_window_title"])
    login_window.geometry("600x400")

    # Progress frame
    frame_progress = ttk.Frame(login_window)
    frame_progress.pack(pady=10, padx=10, fill="x")

    progress_var = tk.DoubleVar()
    progress_bar = ttk.Progressbar(
        frame_progress,
        variable=progress_var,
        maximum=len(folders)
    )
    progress_bar.pack(fill="x")

    # Status label
    status_label = ttk.Label(frame_progress, text="")
    status_label.pack(pady=5)

    # Log frame
    frame_log = ttk.Frame(login_window)
    frame_log.pack(pady=10, padx=10, fill="both", expand=True)

    log_text = tk.Text(frame_log, height=15)
    log_text.pack(fill="both", expand=True)

    scrollbar = ttk.Scrollbar(frame_log, command=log_text.yview)
    scrollbar.pack(side="right", fill="y")
    log_text.configure(yscrollcommand=scrollbar.set)

    def update_progress(current, total, message):
        """Update progress bar and log"""
        progress_var.set(current)
        status_label.config(text=f"{current}/{total} - {message}")
        log_text.insert("end", message + "\n")
        log_text.see("end")
        login_window.update()

    async def login_account(phone, session_path):
        """Login to a single Telegram account"""
        client = None
        try:
            # Create client
            client = TelegramClient(session_path, API_ID, API_HASH)
            
            # Connect
            await client.connect()
            
            # Check if already authorized
            if await client.is_user_authorized():
                return True, "Already authorized"

            # Send code request
            await client.send_code_request(phone)
            
            # Get verification code
            code = None
            while not code:
                code = get_verification_code(login_window, phone)
                if not code:
                    raise Exception("Code entry cancelled")
            
            # Sign in
            try:
                await client.sign_in(phone, code)
            except SessionPasswordNeededError:
                # 2FA needed
                password = None
                while not password:
                    password = get_2fa_password(login_window, phone)
                    if not password:
                        raise Exception("2FA entry cancelled")
                await client.sign_in(password=password)
            
            return True, "Login successful"

        except PhoneNumberInvalidError:
            return False, "Invalid phone number"
        except ApiIdInvalidError:
            return False, "Invalid API credentials"
        except PhoneCodeInvalidError:
            return False, "Invalid verification code"
        except Exception as e:
            return False, str(e)
        finally:
            if client:
                await client.disconnect()

    async def process_accounts():
        """Process all accounts for login"""
        successful = 0
        failed = 0
        
        for i, folder in enumerate(folders, 1):
            phone = os.path.basename(folder)
            session_path = os.path.join(folder, "session")
            
            # Clean up any existing session
            cleanup_session_files(session_path)
            
            update_progress(i-1, len(folders),
                          f"Processing {phone}...")
            
            success, message = await login_account(phone, session_path)
            
            if success:
                successful += 1
                update_progress(i, len(folders),
                              f"✅ {phone}: {message}")
            else:
                failed += 1
                update_progress(i, len(folders),
                              f"❌ {phone}: {message}")
        
        # Show final results
        final_message = (
            f"Completed!\n"
            f"Successful: {successful}\n"
            f"Failed: {failed}"
        )
        messagebox.showinfo("Kết quả", final_message)
        login_window.destroy()

    # Start processing
    asyncio.run(process_accounts())

def get_verification_code(parent, phone):
    """Show dialog to get verification code"""
    dialog = tk.Toplevel(parent)
    dialog.title(lang["verification_title"])
    dialog.geometry("300x150")
    
    ttk.Label(dialog,
             text=f"{lang['enter_code']}\n{phone}").pack(pady=10)
    
    code_var = tk.StringVar()
    code_entry = ttk.Entry(dialog, textvariable=code_var)
    code_entry.pack(pady=10)
    code_entry.focus()
    
    result = [None]
    
    def on_submit():
        result[0] = code_var.get().strip()
        dialog.destroy()
    
    def on_cancel():
        dialog.destroy()
    
    ttk.Button(dialog, text=lang["submit"],
               command=on_submit).pack(side="left", padx=10)
    ttk.Button(dialog, text=lang["cancel"],
               command=on_cancel).pack(side="right", padx=10)
    
    dialog.transient(parent)
    dialog.grab_set()
    parent.wait_window(dialog)
    
    return result[0]

def get_2fa_password(parent, phone):
    """Show dialog to get 2FA password"""
    dialog = tk.Toplevel(parent)
    dialog.title(lang["2fa_title"])
    dialog.geometry("300x150")
    
    ttk.Label(dialog,
             text=f"{lang['enter_2fa']}\n{phone}").pack(pady=10)
    
    pass_var = tk.StringVar()
    pass_entry = ttk.Entry(dialog, textvariable=pass_var, show="*")
    pass_entry.pack(pady=10)
    pass_entry.focus()
    
    result = [None]
    
    def on_submit():
        result[0] = pass_var.get().strip()
        dialog.destroy()
    
    def on_cancel():
        dialog.destroy()
    
    ttk.Button(dialog, text=lang["submit"],
               command=on_submit).pack(side="left", padx=10)
    ttk.Button(dialog, text=lang["cancel"],
               command=on_cancel).pack(side="right", padx=10)
    
    dialog.transient(parent)
    dialog.grab_set()
    parent.wait_window(dialog)
    
    return result[0] 