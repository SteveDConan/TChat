import os
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from core.config import (
    WINDOW_SIZE_FILE, CHATGPT_API_KEY_FILE,
    DEFAULT_TELEGRAM_PATH, DEFAULT_TARGET_LANG,
    TRANSLATION_ONLY
)
from core.language import lang

def open_settings():
    """Open settings window"""
    settings_window = tk.Toplevel()
    settings_window.title(lang["settings_title"])
    settings_window.geometry("500x600")

    # Create notebook for tabs
    notebook = ttk.Notebook(settings_window)
    notebook.pack(fill="both", expand=True, padx=10, pady=5)

    # General settings tab
    general_frame = ttk.Frame(notebook)
    notebook.add(general_frame, text=lang["general_settings"])

    # Window size settings
    size_frame = ttk.LabelFrame(general_frame, text=lang["window_size"])
    size_frame.pack(fill="x", padx=5, pady=5)

    # Width entry
    width_frame = ttk.Frame(size_frame)
    width_frame.pack(fill="x", padx=5, pady=5)
    ttk.Label(width_frame, text=lang["window_width"]).pack(side="left")
    width_entry = ttk.Entry(width_frame)
    width_entry.pack(side="right", expand=True)

    # Height entry
    height_frame = ttk.Frame(size_frame)
    height_frame.pack(fill="x", padx=5, pady=5)
    ttk.Label(height_frame, text=lang["window_height"]).pack(side="left")
    height_entry = ttk.Entry(height_frame)
    height_entry.pack(side="right", expand=True)

    # Load current window size
    try:
        if os.path.exists(WINDOW_SIZE_FILE):
            with open(WINDOW_SIZE_FILE, "r") as f:
                size_data = json.load(f)
                width_entry.insert(0, str(size_data.get("width", 500)))
                height_entry.insert(0, str(size_data.get("height", 600)))
    except Exception as e:
        print(f"Consolog [ERROR]: Không thể đọc cấu hình kích thước cửa sổ: {e}")
        width_entry.insert(0, "500")
        height_entry.insert(0, "600")

    # Telegram path settings
    path_frame = ttk.LabelFrame(general_frame, text=lang["telegram_path_settings"])
    path_frame.pack(fill="x", padx=5, pady=5)

    path_entry = ttk.Entry(path_frame)
    path_entry.pack(side="left", fill="x", expand=True, padx=5, pady=5)
    path_entry.insert(0, DEFAULT_TELEGRAM_PATH)

    def browse_telegram():
        file_path = filedialog.askopenfilename(
            title=lang["choose_telegram"],
            filetypes=[("Telegram", "Telegram.exe"), ("All files", "*.*")]
        )
        if file_path:
            path_entry.delete(0, tk.END)
            path_entry.insert(0, file_path)

    ttk.Button(path_frame, text=lang["browse"],
               command=browse_telegram).pack(side="right", padx=5, pady=5)

    # ChatGPT settings tab
    chatgpt_frame = ttk.Frame(notebook)
    notebook.add(chatgpt_frame, text="ChatGPT")

    # API key settings
    api_frame = ttk.LabelFrame(chatgpt_frame, text=lang["api_key_settings"])
    api_frame.pack(fill="x", padx=5, pady=5)

    api_entry = ttk.Entry(api_frame, show="*")
    api_entry.pack(fill="x", padx=5, pady=5)

    # Load current API key
    try:
        if os.path.exists(CHATGPT_API_KEY_FILE):
            with open(CHATGPT_API_KEY_FILE, "r") as f:
                api_entry.insert(0, f.read().strip())
    except Exception as e:
        print(f"Consolog [ERROR]: Không thể đọc API key: {e}")

    # Translation settings
    trans_frame = ttk.LabelFrame(chatgpt_frame, text=lang["translation_settings"])
    trans_frame.pack(fill="x", padx=5, pady=5)

    # Target language
    lang_frame = ttk.Frame(trans_frame)
    lang_frame.pack(fill="x", padx=5, pady=5)
    ttk.Label(lang_frame, text=lang["target_lang"]).pack(side="left")
    lang_var = tk.StringVar(value=DEFAULT_TARGET_LANG)
    lang_combo = ttk.Combobox(lang_frame, textvariable=lang_var,
                             values=["vi", "en", "zh"])
    lang_combo.pack(side="right", expand=True)

    # Translation only mode
    trans_only_var = tk.BooleanVar(value=TRANSLATION_ONLY)
    trans_only_check = ttk.Checkbutton(
        trans_frame,
        text=lang["translation_only"],
        variable=trans_only_var
    )
    trans_only_check.pack(padx=5, pady=5)

    def save_settings():
        """Save all settings"""
        try:
            # Save window size
            width = int(width_entry.get())
            height = int(height_entry.get())
            with open(WINDOW_SIZE_FILE, "w") as f:
                json.dump({"width": width, "height": height}, f)

            # Save Telegram path
            telegram_path = path_entry.get()
            if not os.path.exists(telegram_path):
                messagebox.showerror("Lỗi", lang["msg_invalid_telegram_path"])
                return

            # Save API key
            api_key = api_entry.get().strip()
            if api_key:
                with open(CHATGPT_API_KEY_FILE, "w") as f:
                    f.write(api_key)

            # Save translation settings
            translation_settings = {
                "target_lang": lang_var.get(),
                "translation_only": trans_only_var.get()
            }
            with open("translation_settings.json", "w") as f:
                json.dump(translation_settings, f)

            messagebox.showinfo("Thành công", lang["msg_settings_saved"])
            settings_window.destroy()

        except ValueError:
            messagebox.showerror("Lỗi", lang["msg_invalid_window_size"])
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi lưu cấu hình: {str(e)}")

    # Save button
    ttk.Button(settings_window, text=lang["save_settings"],
               command=save_settings).pack(pady=10)

    # Center window
    settings_window.update_idletasks()
    width = settings_window.winfo_width()
    height = settings_window.winfo_height()
    x = (settings_window.winfo_screenwidth() - width) // 2
    y = (settings_window.winfo_screenheight() - height) // 2
    settings_window.geometry(f"{width}x{height}+{x}+{y}")

    settings_window.transient(settings_window.master)
    settings_window.grab_set()
    settings_window.focus_set() 