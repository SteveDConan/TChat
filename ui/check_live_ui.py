import os
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from datetime import datetime

from core.language import lang
from core.telegram_utils import (
    open_telegram_window,
    close_telegram_window,
    arrange_telegram_windows,
    capture_window,
    compare_images_with_marker
)

def warn_check_live():
    """Show warning before checking live status"""
    warning_msg = (
        "【Tiếng Việt】: Quá trình kiểm tra trạng thái trực tiếp sẽ mở các cửa sổ Telegram "
        "và kiểm tra từng tài khoản. Vui lòng không tương tác với máy tính trong quá trình này.\n"
        "【English】: The live status check process will open Telegram windows and check each "
        "account. Please do not interact with your computer during this process.\n"
        "【中文】: 实时状态检查过程将打开 Telegram 窗口并检查每个账户。"
        "在此过程中请勿与计算机进行交互。"
    )
    response = messagebox.askokcancel("Cảnh báo", warning_msg)
    if response:
        check_live_status()

def check_live_status():
    """Check live status of all Telegram accounts"""
    # Create check live window
    check_window = tk.Toplevel()
    check_window.title(lang["check_live_title"])
    check_window.geometry("600x400")

    # Progress frame
    frame_progress = ttk.Frame(check_window)
    frame_progress.pack(pady=10, padx=10, fill="x")

    progress_var = tk.DoubleVar()
    progress_bar = ttk.Progressbar(
        frame_progress,
        variable=progress_var,
        maximum=100
    )
    progress_bar.pack(fill="x")

    # Status label
    status_label = ttk.Label(frame_progress, text="")
    status_label.pack(pady=5)

    # Results frame
    frame_results = ttk.Frame(check_window)
    frame_results.pack(pady=10, padx=10, fill="both", expand=True)

    results_text = tk.Text(frame_results, height=15)
    results_text.pack(fill="both", expand=True)

    scrollbar = ttk.Scrollbar(frame_results, command=results_text.yview)
    scrollbar.pack(side="right", fill="y")
    results_text.configure(yscrollcommand=scrollbar.set)

    def update_progress(current, total, message):
        """Update progress bar and log"""
        progress = (current / total) * 100
        progress_var.set(progress)
        status_label.config(text=f"{current}/{total} - {message}")
        results_text.insert("end", message + "\n")
        results_text.see("end")
        check_window.update()

    def check_account(telegram_path, account_folder):
        """Check live status for a single account"""
        try:
            # Open Telegram window
            hwnd = open_telegram_window(telegram_path, account_folder)
            if not hwnd:
                return False, "Failed to open Telegram window"

            # Wait for window to load
            time.sleep(5)

            # Capture window content
            screenshot = capture_window(hwnd)
            if not screenshot:
                return False, "Failed to capture window"

            # Compare with marker image
            is_live = compare_images_with_marker(screenshot)

            # Close window
            close_telegram_window(hwnd)

            return True, "Live" if is_live else "Not live"

        except Exception as e:
            return False, str(e)

    def process_accounts():
        """Process all accounts for live checking"""
        tdata_folders = []  # Get list of TData folders
        total = len(tdata_folders)
        live_count = 0
        dead_count = 0
        error_count = 0

        for i, folder in enumerate(tdata_folders, 1):
            phone = os.path.basename(folder)
            update_progress(i, total, f"Checking {phone}...")

            success, status = check_account(telegram_path, folder)
            
            if success:
                if status == "Live":
                    live_count += 1
                    update_progress(i, total, f"✅ {phone}: Live")
                else:
                    dead_count += 1
                    update_progress(i, total, f"❌ {phone}: Not live")
            else:
                error_count += 1
                update_progress(i, total, f"⚠️ {phone}: Error - {status}")

            # Small delay between accounts
            time.sleep(2)

        # Generate report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = f"check_live_report_{timestamp}.txt"
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(f"Live Check Report - {datetime.now()}\n")
            f.write("-" * 40 + "\n")
            f.write(f"Total accounts checked: {total}\n")
            f.write(f"Live accounts: {live_count}\n")
            f.write(f"Dead accounts: {dead_count}\n")
            f.write(f"Errors: {error_count}\n")
            f.write("-" * 40 + "\n")
            f.write(results_text.get("1.0", "end"))

        # Show final results
        final_message = (
            f"Check completed!\n"
            f"Live: {live_count}\n"
            f"Dead: {dead_count}\n"
            f"Errors: {error_count}\n\n"
            f"Report saved to: {report_path}"
        )
        messagebox.showinfo("Kết quả", final_message)
        check_window.destroy()

    # Start processing in a separate thread
    threading.Thread(target=process_accounts, daemon=True).start() 