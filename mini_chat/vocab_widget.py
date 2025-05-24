import tkinter as tk
import json
import datetime
import threading


class VocabWidget(tk.Frame):
    """
    Widget học từ vựng cho mỗi ngày, đổi từ tự động 15 giây.
    Đọc dữ liệu từ 1 file JSON dạng {"1": [...], ..., "31": [...]}
    """

    def __init__(
        self, parent, vocab_file="mini_chat/vocabs/vocab_all.json", width=250, height=38
    ):
        super().__init__(parent, width=width, height=height)
        self.pack_propagate(0)
        self.width = width
        self.height = height
        self.vocab_file = vocab_file
        self.current_idx = 0
        self.vocab_list = self.load_today_vocab()

        # Label từ vựng + nghĩa
        # Label từ vựng + nghĩa, căn giữa
        self.label_word = tk.Label(
            self, 
            text="", 
            font=("Segoe UI", 9, "bold"), 
            anchor="center",      # Căn giữa theo khung
            # justify="center",     # Căn giữa các dòng nếu xuống dòng
            wraplength=width
        )
        self.label_word.pack(fill=tk.X, padx=2)
        # Label câu ví dụ
        self.label_example = tk.Label(
            self, text="", font=("Segoe UI", 8), fg="#777", anchor="center", wraplength=width
        )
        self.label_example.pack(fill=tk.X, padx=2,pady=(0, 4))

        self.after(100, self.display_vocab)
        self.start_auto_change()

    def load_today_vocab(self):
        """Đọc dữ liệu ngày hôm nay từ file json (dạng dict: ngày -> list từ)."""
        today = str(datetime.datetime.now().day)
        print("Consolog: Ngày hệ thống hiện tại là:", today)
        try:
            with open(self.vocab_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                print("Consolog: Đã đọc được các ngày trong file:", list(data.keys()))
            if isinstance(data, dict):
                vocab_today = data.get(today, [])
                print("Consolog: Số lượng từ vựng lấy ra:", len(vocab_today))
            else:
                vocab_today = []
            return vocab_today
        except Exception as e:
            print(f"Consolog: Lỗi khi đọc file vocab: {e}")
            return []

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

    def next_vocab(self):
        """Chuyển sang từ tiếp theo."""
        if self.vocab_list:
            self.current_idx = (self.current_idx + 1) % len(self.vocab_list)
            self.display_vocab()

    def start_auto_change(self):
        """Tự động đổi từ sau mỗi 5 giây."""

        def run():
            while True:
                self.after(0, self.next_vocab)
                threading.Event().wait(5)

        threading.Thread(target=run, daemon=True).start()
