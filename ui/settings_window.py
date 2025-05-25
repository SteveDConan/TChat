# ui/settings_window.py

import tkinter as tk
from tkinter import messagebox

def create_settings_window(
    root,
    arrange_width,
    arrange_height,
    save_window_size,
    load_chatgpt_api_key,
    save_chatgpt_api_key,
    DEFAULT_TARGET_LANG,
    set_default_target_lang_callback
):
    """
    Tạo popup cấu hình cài đặt: Sắp xếp cửa sổ, ChatGPT API Key, ngôn ngữ dịch mặc định.

    Args:
        root: Tk root window.
        arrange_width, arrange_height: giá trị width/height mặc định.
        save_window_size: callback lưu width/height.
        load_chatgpt_api_key: callback lấy API key hiện tại.
        save_chatgpt_api_key: callback lưu API key mới.
        DEFAULT_TARGET_LANG: biến lưu target lang hiện tại.
        set_default_target_lang_callback: callback cập nhật target lang (nếu cần).
    """
    popup = tk.Toplevel(root)
    popup.title("Setting - Tùy chỉnh sắp xếp & ChatGPT")
    popup.geometry("400x350")
    popup.transient(root)
    popup.grab_set()

    tk.Label(
        popup, 
        text="Nhập kích thước cửa sổ sắp xếp:\nx = (số cột) × Custom Width, y = (số hàng) × Custom Height", 
        wraplength=380
    ).pack(pady=10)

    frame_entries = tk.Frame(popup)
    frame_entries.pack(pady=5)

    tk.Label(frame_entries, text="Custom Width:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
    entry_width = tk.Entry(frame_entries, width=10)
    entry_width.insert(0, str(arrange_width))
    entry_width.grid(row=0, column=1, padx=5, pady=5)

    tk.Label(frame_entries, text="Custom Height:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
    entry_height = tk.Entry(frame_entries, width=10)
    entry_height.insert(0, str(arrange_height))
    entry_height.grid(row=1, column=1, padx=5, pady=5)

    # ChatGPT API key entry
    tk.Label(popup, text="ChatGPT API Key:").pack(pady=5)
    chatgpt_key_entry = tk.Entry(popup, width=50)
    chatgpt_key_entry.insert(0, load_chatgpt_api_key())
    chatgpt_key_entry.pack(pady=5)

    # Ngôn ngữ đích dịch
    tk.Label(popup, text="Default Translation Language (Target):").pack(pady=5)
    translation_lang_var = tk.StringVar(value=DEFAULT_TARGET_LANG)
    translation_lang_menu = tk.OptionMenu(popup, translation_lang_var, "vi", "en", "zh")
    translation_lang_menu.pack(pady=5)

    def save_settings():
        try:
            w = int(entry_width.get())
            h = int(entry_height.get())
            save_window_size(w, h)

            save_chatgpt_api_key(chatgpt_key_entry.get().strip())

            # Gọi callback cập nhật ngôn ngữ đích nếu truyền vào
            if set_default_target_lang_callback:
                set_default_target_lang_callback(translation_lang_var.get())

            messagebox.showinfo("Setting", "Đã lưu cấu hình!")
            popup.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Giá trị không hợp lệ: {e}")

    btn_save = tk.Button(popup, text="Save", command=save_settings)
    btn_save.pack(pady=10)

    popup.wait_window()
