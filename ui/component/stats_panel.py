import tkinter as tk


class StatsPanel(tk.Frame):
    """
    Panel hiển thị thống kê folder TData:
    - Hiển thị tổng quan các thư mục con
    - Thống kê số lượng tdata, tên thư mục
    - Chỉ là UI, không tự ý đi duyệt ổ cứng!
    """

    def __init__(self, parent, lang=None, *args, **kwargs):
        """
        Args:
            parent: Widget cha (MainWindow)
            lang: dict ngôn ngữ đa ngữ (tùy chọn)
        """
        super().__init__(parent, *args, **kwargs)
        self.lang = lang or {"stats_label": "Thống kê TData"}

        # Tiêu đề
        self.label_stats = tk.Label(self, text=self.lang.get("stats_label", "Stats"))
        self.label_stats.pack(anchor="w", padx=5, pady=(0, 2))

        # Vùng text hiển thị thống kê
        self.text_stats = tk.Text(self, width=70, height=10, state=tk.DISABLED)
        self.text_stats.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)

    def update_stats(self, info_text):
        """
        Cập nhật lại nội dung thống kê.
        Args:
            info_text (str): Chuỗi thống kê đã format sẵn (từ MainWindow)
        """
        self.text_stats.config(state=tk.NORMAL)
        self.text_stats.delete("1.0", tk.END)
        self.text_stats.insert(tk.END, info_text)
        self.text_stats.config(state=tk.DISABLED)

    def clear(self):
        """
        Xóa nội dung thống kê.
        """
        self.text_stats.config(state=tk.NORMAL)
        self.text_stats.delete("1.0", tk.END)
        self.text_stats.config(state=tk.DISABLED)
