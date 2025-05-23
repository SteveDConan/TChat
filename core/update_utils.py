import os
import requests
from distutils.version import LooseVersion
import tkinter as tk
from tkinter import ttk, messagebox

from .config import CURRENT_VERSION, GITHUB_USER, GITHUB_REPO
from .language import lang

def check_for_updates(root):
    """Check for updates from GitHub releases"""
    print("Consolog: Kiểm tra cập nhật phiên bản...")
    try:
        url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/releases/latest"
        response = requests.get(url)
        
        if response.status_code == 200:
            release_info = response.json()
            latest_version = release_info["tag_name"].lstrip("v")
            print(f"Consolog: Phiên bản mới nhất từ GitHub: {latest_version}")
            
            if LooseVersion(latest_version) > LooseVersion(CURRENT_VERSION):
                if messagebox.askyesno(
                    "Cập nhật",
                    lang["update_available"].format(version=latest_version)
                ):
                    print("Consolog [UPDATE]: Người dùng chọn cập nhật phiên bản mới.")
                    assets = release_info.get("assets", [])
                    download_url = None
                    
                    for asset in assets:
                        if asset["name"].lower().endswith(".exe"):
                            download_url = asset["browser_download_url"]
                            break
                    
                    if not download_url and assets:
                        download_url = assets[0]["browser_download_url"]
                    
                    if download_url:
                        print(f"Consolog [UPDATE]: Bắt đầu tải file cập nhật từ {download_url}")
                        download_update_with_progress(download_url, root)
                    else:
                        messagebox.showerror("Error", "Không tìm thấy file cập nhật trên GitHub.")
                        print("Consolog [UPDATE ERROR]: Không tìm thấy asset cập nhật.")
                else:
                    print("Consolog [UPDATE]: Người dùng không cập nhật.")
            else:
                messagebox.showinfo("Cập nhật", lang["no_updates"])
                print("Consolog: Bạn đang dùng phiên bản mới nhất.")
        else:
            messagebox.showerror("Error", lang["update_error"])
            print("Consolog: Lỗi kiểm tra cập nhật.")
    except Exception as e:
        messagebox.showerror("Error", f"Lỗi kiểm tra cập nhật: {e}")
        print(f"Consolog [ERROR]: Lỗi kiểm tra cập nhật: {e}")

def download_update_with_progress(download_url, root):
    """Download update with progress bar"""
    local_filename = download_url.split("/")[-1]
    print(f"Consolog [UPDATE]: Đang tải xuống file: {local_filename}")

    # Create progress window
    progress_win = tk.Toplevel(root)
    progress_win.title("Đang tải cập nhật")
    progress_win.geometry("550x130")

    # Create custom style for progress bar
    style = ttk.Style(progress_win)
    style.configure("Custom.Horizontal.TProgressbar",
                   troughcolor="white",
                   background="blue",
                   thickness=20)

    # Setup progress UI
    tk.Label(progress_win, text=f"Đang tải: {local_filename}").pack(pady=5)
    progress_var = tk.DoubleVar(value=0)
    progress_bar = ttk.Progressbar(
        progress_win,
        variable=progress_var,
        maximum=100,
        length=500,
        style="Custom.Horizontal.TProgressbar"
    )
    progress_bar.pack(pady=5)
    percent_label = tk.Label(progress_win, text="0%")
    percent_label.pack(pady=5)
    progress_win.update()

    try:
        # Start download
        response = requests.get(download_url, stream=True)
        total_length = response.headers.get('content-length')
        
        if total_length is None:
            messagebox.showerror("Error", "Không xác định được kích thước file cập nhật.")
            print("Consolog [UPDATE ERROR]: Không xác định được content-length.")
            progress_win.destroy()
            return
        
        total_length = int(total_length)
        downloaded = 0
        
        with open(local_filename, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    percent = (downloaded / total_length) * 100
                    progress_var.set(percent)
                    percent_label.config(text=f"{int(percent)}%")
                    progress_win.update_idletasks()

        progress_win.destroy()

        # Show completion notification
        notify_win = tk.Toplevel(root)
        notify_win.title("Tải cập nhật thành công")
        tk.Label(notify_win, text=f"Đã tải xong {local_filename}").pack(pady=10)

        def open_update_folder():
            folder = os.path.abspath(os.getcwd())
            try:
                os.startfile(folder)
            except Exception as e:
                messagebox.showerror("Error", f"Lỗi mở thư mục: {e}")

        tk.Button(notify_win, text="Mở vị trí file cập nhật",
                 command=open_update_folder).pack(pady=5)
        tk.Button(notify_win, text="Close",
                 command=notify_win.destroy).pack(pady=5)
        
        print("Consolog [UPDATE]: Tải về cập nhật hoàn tất.")
    
    except Exception as e:
        messagebox.showerror("Error", f"Failed to download update: {e}")
        print(f"Consolog [UPDATE ERROR]: Lỗi tải cập nhật: {e}")
        progress_win.destroy() 