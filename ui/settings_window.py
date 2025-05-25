import tkinter as tk
from tkinter import messagebox


class SettingsWindow(tk.Toplevel):
    """
    Popup cài đặt (settings): cho phép người dùng điều chỉnh các thông số cấu hình chính.
    - Kích thước cửa sổ sắp xếp Telegram
    - ChatGPT API Key
    - Ngôn ngữ dịch mặc định
    """

    def __init__(
        self,
        master,
        arrange_width=500,
        arrange_height=504,
        chatgpt_api_key="",
        default_target_lang="vi",
        on_save_callback=None,  # callback truyền về MainWindow nếu muốn
        lang=None,
    ):
        super().__init__(master)
        self.title("Setting - Tùy chỉnh sắp xếp & ChatGPT")
        self.geometry("400x350")
        self.resizable(False, False)

        self.arrange_width = tk.IntVar(value=arrange_width)
        self.arrange_height = tk.IntVar(value=arrange_height)
        self.chatgpt_api_key = tk.StringVar(value=chatgpt_api_key)
        self.default_target_lang = tk.StringVar(value=default_target_lang)
        self.on_save_callback = on_save_callback
        self.lang = lang or {
            "setting_saved": "Đã lưu cấu hình thành công!",
            "error_invalid_value": "Giá trị không hợp lệ!",
        }

        # ----- Giao diện -----
        info_lbl = tk.Label(
            self,
            text="Nhập kích thước cửa sổ sắp xếp:\nx = (số cột) × Custom Width, y = (số hàng) × Custom Height",
            wraplength=380,
        )
        info_lbl.pack(pady=10)

        # Frame nhập width/height
        frame_entries = tk.Frame(self)
        frame_entries.pack(pady=5)

        tk.Label(frame_entries, text="Custom Width:").grid(
            row=0, column=0, padx=5, pady=5, sticky="e"
        )
        entry_width = tk.Entry(frame_entries, textvariable=self.arrange_width, width=10)
        entry_width.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(frame_entries, text="Custom Height:").grid(
            row=1, column=0, padx=5, pady=5, sticky="e"
        )
        entry_height = tk.Entry(
            frame_entries, textvariable=self.arrange_height, width=10
        )
        entry_height.grid(row=1, column=1, padx=5, pady=5)

        # Nhập ChatGPT API Key
        tk.Label(self, text="ChatGPT API Key:").pack(pady=5)
        chatgpt_key_entry = tk.Entry(self, textvariable=self.chatgpt_api_key, width=50)
        chatgpt_key_entry.pack(pady=5)

        # Ngôn ngữ mặc định
        tk.Label(self, text="Default Translation Language (Target):").pack(pady=5)
        translation_lang_menu = tk.OptionMenu(
            self, self.default_target_lang, "vi", "en", "zh"
        )
        translation_lang_menu.pack(pady=5)

        # Nút Save
        btn_save = tk.Button(self, text="Save", command=self.save_settings)
        btn_save.pack(pady=10)

        # Đảm bảo popup modal (block main window cho đến khi đóng settings)
        self.transient(master)
        self.grab_set()
        self.wait_window(self)

    def save_settings(self):
        """
        Lưu lại các giá trị cấu hình khi bấm Save. Gọi callback nếu có.
        """
        try:
            w = int(self.arrange_width.get())
            h = int(self.arrange_height.get())
            api_key = self.chatgpt_api_key.get().strip()
            lang = self.default_target_lang.get()

            # Thực hiện lưu thực tế (gọi callback hoặc lưu ra file nếu muốn)
            if self.on_save_callback:
                self.on_save_callback(
                    {
                        "arrange_width": w,
                        "arrange_height": h,
                        "chatgpt_api_key": api_key,
                        "default_target_lang": lang,
                    }
                )

            messagebox.showinfo(
                "Setting", self.lang.get("setting_saved", "Đã lưu cấu hình!")
            )
            self.destroy()
        except Exception as e:
            messagebox.showerror(
                "Error",
                f'{self.lang.get("error_invalid_value", "Giá trị không hợp lệ!")}: {e}',
            )
