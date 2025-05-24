import tkinter as tk
import json
import datetime

class VocabWidget(tk.Frame):
    """
    Widget học từ vựng cho mỗi ngày, đổi từ tự động 5 giây.
    Đọc dữ liệu từ 1 file JSON dạng {"1": [...], ..., "31": [...]}
    """
    def __init__(
        self, parent, vocab_file="mini_chat/vocabs/vocab_all.json", width=250, height=54
    ):
        super().__init__(parent, width=width, height=height)
        self.pack_propagate(0)
        self.width = width
        self.height = height
        self.vocab_file = vocab_file
        self.current_idx = 0
        self.vocab_list = self.load_today_vocab()

        self.progress_time = 5  # số giây hiển thị mỗi từ
        self.progress_update_ms = 30  # 30ms cập nhật progress 1 lần

        # Label từ vựng + nghĩa, căn giữa
        self.label_word = tk.Label(
            self, text="", font=("Segoe UI", 9, "bold"),
            anchor="center", wraplength=width
        )
        self.label_word.pack(fill=tk.X, padx=2)

        # Label câu ví dụ
        self.label_example = tk.Label(
            self, text="", font=("Segoe UI", 8), fg="#777",
            anchor="center", wraplength=width
        )
        self.label_example.pack(fill=tk.X, padx=2, pady=(0, 2))

        # Thanh progress nhỏ
        self.progress_canvas = tk.Canvas(self, width=width, height=2, bg="#e0e0e0", highlightthickness=0)
        self.progress_canvas.pack(fill=tk.X, pady=(0, 0))
        self.progress_bar = self.progress_canvas.create_rectangle(
            0, 0, 0, 2, fill="#4CAF50", width=0
        )

        self._timer_id = None      # Lưu ID after để cancel khi cần
        self._progress_elapsed = 0 # Số ms đã trôi qua

        self.display_and_progress() # Khởi động vòng lặp

    def load_today_vocab(self):
        today = str(datetime.datetime.now().day)
        try:
            with open(self.vocab_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                vocab_today = data.get(today, [])
            else:
                vocab_today = []
            return vocab_today
        except Exception as e:
            print(f"Lỗi khi đọc file vocab: {e}")
            return []

    def display_and_progress(self):
        """Đổi từ, reset progress bar, và bắt đầu chạy tiến trình"""
        self.display_vocab()
        self._progress_elapsed = 0
        self.update_progress_bar()
        
    def display_vocab(self):
        """Hiển thị từ vựng hiện tại."""
        if not self.vocab_list:
            self.label_word.config(text="Không có dữ liệu từ vựng.")
            self.label_example.config(text="")
            return
        word_info = self.vocab_list[self.current_idx]
        word = word_info.get("word", "")
        word_type = word_info.get("type", "")
        meaning = word_info.get("meaning", "")
        example = word_info.get("example", "")
        text_top = f"{word} ({word_type}) : {meaning}"
        self.label_word.config(text=text_top)
        self.label_example.config(text=example)

    def update_progress_bar(self):
        """Cập nhật thanh tiến trình và tự động chuyển từ khi đủ thời gian"""
        percent = self._progress_elapsed / (self.progress_time * 1000)
        fill_width = int(self.width * percent)
        self.progress_canvas.coords(self.progress_bar, 0, 0, fill_width, 2)

        if self._progress_elapsed < self.progress_time * 1000:
            self._progress_elapsed += self.progress_update_ms
            self._timer_id = self.after(self.progress_update_ms, self.update_progress_bar)
        else:
            self.next_vocab()
            self.display_and_progress()

    def next_vocab(self):
        """Chuyển sang từ tiếp theo."""
        if self.vocab_list:
            self.current_idx = (self.current_idx + 1) % len(self.vocab_list)

    def destroy(self):
        # Hủy timer khi đóng widget để tránh lỗi callback
        if self._timer_id:
            self.after_cancel(self._timer_id)
        super().destroy()
