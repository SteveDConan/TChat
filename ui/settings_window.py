import tkinter as tk
from tkinter import messagebox

class SettingsWindow(tk.Toplevel):
    """
    Cửa sổ cấu hình Settings (window size, API Key, ngôn ngữ...)
    """
    def __init__(self, master, arrange_width, arrange_height, chatgpt_api_key, default_target_lang, on_save_settings):
        super().__init__(master)
        self.title("Setting - Tùy chỉnh sắp xếp & ChatGPT")
        self.arrange_width = arrange_width
        self.arrange_height = arrange_height
        self.chatgpt_api_key = chatgpt_api_key
        self.default_target_lang = default_target_lang
        self.on_save_settings = on_save_settings

        self.geometry("400x350")
        lbl_info = tk.Label(self, text="Nhập kích thước cửa sổ sắp xếp:\nx = (số cột) × Custom Width, y = (số hàng) × Custom Height", wraplength=380)
        lbl_info.pack(pady=10)

        frame_entries = tk.Frame(self)
        frame_entries.pack(pady=5)

        tk.Label(frame_entries, text="Custom Width:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.entry_width = tk.Entry(frame_entries, width=10)
        self.entry_width.insert(0, str(arrange_width))
        self.entry_width.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(frame_entries, text="Custom Height:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.entry_height = tk.Entry(frame_entries, width=10)
        self.entry_height.insert(0, str(arrange_height))
        self.entry_height.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(self, text="ChatGPT API Key:").pack(pady=5)
        self.chatgpt_key_entry = tk.Entry(self, width=50)
        self.chatgpt_key_entry.insert(0, chatgpt_api_key)
        self.chatgpt_key_entry.pack(pady=5)

        tk.Label(self, text="Default Translation Language (Target):").pack(pady=5)
        self.translation_lang_var = tk.StringVar(value=default_target_lang)
        translation_lang_menu = tk.OptionMenu(self, self.translation_lang_var, "vi", "en", "zh")
        translation_lang_menu.pack(pady=5)

        btn_save = tk.Button(self, text="Save", command=self.save_settings)
        btn_save.pack(pady=10)

    def save_settings(self):
        try:
            w = int(self.entry_width.get())
            h = int(self.entry_height.get())
            key = self.chatgpt_key_entry.get().strip()
            lang = self.translation_lang_var.get()
            # Gọi callback lưu config truyền từ ngoài vào
            self.on_save_settings(w, h, key, lang)
            messagebox.showinfo("Setting", "Đã lưu cấu hình!")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Giá trị không hợp lệ: {e}")
