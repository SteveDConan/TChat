import tkinter as tk


class LogPanel(tk.Frame):
    """
    Panel hiển thị log trạng thái ứng dụng.
    - Gồm: tiêu đề log, vùng hiển thị log (Text), có thể mở rộng thêm nút xóa.
    """

    def __init__(self, parent, lang=None, *args, **kwargs):
        """
        Args:
            parent: Widget cha (thường là MainWindow).
            lang: dict đa ngôn ngữ (tùy chọn).
        """
        super().__init__(parent, *args, **kwargs)
        self.lang = lang or {"log_label": "Log"}

        # Tiêu đề log
        self.label_log = tk.Label(self, text=self.lang.get("log_label", "Log"))
        self.label_log.pack(anchor="w", padx=5, pady=(0, 2))

        # Vùng text log
        self.text_log = tk.Text(self, width=70, height=10, state=tk.NORMAL)
        self.text_log.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)

        # Nếu muốn có nút clear log:
        self.btn_clear = tk.Button(self, text="Clear", command=self.clear_log)
        self.btn_clear.pack(anchor="e", padx=5, pady=2)

    def add_log(self, message):
        """
        Thêm một dòng log mới vào panel log.
        Args:
            message (str): Nội dung log.
        """
        self.text_log.config(state=tk.NORMAL)
        self.text_log.insert(tk.END, message + "\n")
        self.text_log.see(tk.END)  # Tự động scroll đến dòng cuối
        self.text_log.config(state=tk.NORMAL)

    def clear_log(self):
        """
        Xóa toàn bộ log.
        """
        self.text_log.config(state=tk.NORMAL)
        self.text_log.delete(1.0, tk.END)
        self.text_log.config(state=tk.NORMAL)

    def set_log(self, content):
        """
        Ghi đè toàn bộ nội dung log (ít dùng, chủ yếu cho debug).
        """
        self.text_log.config(state=tk.NORMAL)
        self.text_log.delete(1.0, tk.END)
        self.text_log.insert(tk.END, content)
        self.text_log.see(tk.END)
        self.text_log.config(state=tk.NORMAL)
