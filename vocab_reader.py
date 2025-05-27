# vocab_reader.py

import tkinter as tk
import json
import os
import ctypes

def get_telegram_window_size():
    user32 = ctypes.windll.user32
    hwnd = None
    win_title = "Telegram"
    max_len = 256
    buf = ctypes.create_unicode_buffer(max_len)

    def enum_windows_callback(hwnd_, lParam):
        user32.GetWindowTextW(hwnd_, buf, max_len)
        if "Telegram" in buf.value:
            nonlocal hwnd
            hwnd = hwnd_
            return False
        return True

    EnumWindows = user32.EnumWindows
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
    EnumWindows(EnumWindowsProc(enum_windows_callback), 0)
    if hwnd:
        rect = ctypes.wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        width = rect.right - rect.left
        height = rect.bottom - rect.top
        return (width, height)
    return (400, 600)

class VocabReaderWindow:
    def __init__(self, root, vocab_json="mini_chat/vocabs/vocab_all.json", default_width=400):
        self.root = root
        self.vocab_json = vocab_json
        self.width = default_width
        self.window = None
        self.is_running = False
        self.paused = False
        self.canvas = None
        self.vocabs = []
        self.items = []
        self.scroll_speed = 0.5   # px mỗi frame, rất mượt
        self.font_size = 12
        self.line_gap = 4         # Khoảng cách giữa 2 từ vựng
        self.frame_interval = 10  # ms, ~100fps mượt
        self.text_height = None   # Sẽ tính toán tự động
        self.window_height = None

    def load_vocab(self):
        if not os.path.exists(self.vocab_json):
            return []
        with open(self.vocab_json, "r", encoding="utf-8") as f:
            data = json.load(f)
        vocabs = []
        for v in data.values():
            vocabs.extend(v)
        return vocabs

    def open(self):
        if self.window and tk.Toplevel.winfo_exists(self.window):
            self.window.lift()
            return
        self.vocabs = self.load_vocab()
        if not self.vocabs:
            tk.messagebox.showwarning("Vocab Reader", "Không tìm thấy dữ liệu từ vựng!")
            return

        _, tg_height = get_telegram_window_size()
        self.window_height = tg_height
        self.window = tk.Toplevel(self.root)
        self.window.title("Vocab Reader")
        self.window.geometry(f"{self.width}x{tg_height}")
        self.window.resizable(True, False)
        self.window.attributes("-topmost", True)
        self.window.protocol("WM_DELETE_WINDOW", self.hide)

        def on_resize(event):
            self.width = event.width
            self.canvas.config(width=self.width)
        self.window.bind("<Configure>", on_resize)

        btn_close = tk.Button(self.window, text="Đóng", command=self.hide)
        btn_close.pack(side=tk.BOTTOM, pady=4)

        self.canvas = tk.Canvas(self.window, width=self.width, height=tg_height-30, bg="#181818", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Hover pause/resume
        self.canvas.bind("<Enter>", lambda e: self.set_paused(True))
        self.canvas.bind("<Leave>", lambda e: self.set_paused(False))

        self.is_running = True
        self.paused = False
        self.items = []

        # Tính chiều cao của 1 dòng vocab
        temp_id = self.canvas.create_text(
            self.width//2, 0,
            text=self.build_vocab_line(self.vocabs[0]),
            anchor="n",
            fill="white",
            font=("Arial Unicode MS", self.font_size)
        )
        bbox = self.canvas.bbox(temp_id)
        text_h = (bbox[3] - bbox[1]) if bbox else 32
        self.text_height = text_h + self.line_gap
        self.canvas.delete(temp_id)

        # Khởi tạo text_id cho từng từ, stack dưới cùng trước
        n = len(self.vocabs)
        canvas_h = tg_height - 30

        y = canvas_h + self.text_height  # bắt đầu từ dưới cùng
        self.items.clear()
        for idx, vocab in enumerate(self.vocabs):
            display = self.build_vocab_line(vocab)
            text_id = self.canvas.create_text(
                self.width//2, y,
                text=display,
                anchor="n", fill="white",
                font=("Arial Unicode MS", self.font_size)
            )
            self.items.append((text_id, idx))
            y += self.text_height

        self.scroll_loop()  # bắt đầu loop sau frame_interval

    def build_vocab_line(self, vocab):
        word = vocab.get("word", "")
        word_type = vocab.get("type", "")
        meaning = vocab.get("meaning", "")
        example = vocab.get("example", "")
        return f"{word} ({word_type}) - {meaning}\n{example}"

    def set_paused(self, val):
        self.paused = val

    def hide(self):
        self.is_running = False
        if self.window:
            self.window.destroy()
            self.window = None

    def scroll_loop(self):
        if not self.is_running or not self.window:
            return
        if not self.paused:
            # Move all text up
            for idx, (tid, vocab_idx) in enumerate(self.items):
                self.canvas.move(tid, 0, -self.scroll_speed)
            # Kiểm tra dòng đầu tiên đã đi lên trên thì recyle lại
            top_id, top_vocab_idx = self.items[0]
            x, y = self.canvas.coords(top_id)
            if y < -self.text_height:
                # Lấy vocab tiếp theo
                last_id, last_vocab_idx = self.items[-1]
                last_y = self.canvas.coords(last_id)[1]
                # Xác định vocab kế tiếp, theo vòng tròn
                next_vocab_idx = (self.items[-1][1] + 1) % len(self.vocabs)
                next_vocab = self.vocabs[next_vocab_idx]
                self.canvas.itemconfig(top_id, text=self.build_vocab_line(next_vocab))
                self.items[0] = (top_id, next_vocab_idx)
                self.canvas.coords(top_id, self.width//2, last_y + self.text_height)
                # Đưa xuống cuối hàng
                self.items = self.items[1:] + [self.items[0]]
        self.window.after(self.frame_interval, self.scroll_loop)

# Singleton để dùng ở ngoài
_vocab_reader_instance = None
def open_vocab_reader(root, vocab_json="mini_chat/vocabs/vocab_all.json", width=400):
    global _vocab_reader_instance
    if _vocab_reader_instance is None:
        _vocab_reader_instance = VocabReaderWindow(root, vocab_json, width)
    _vocab_reader_instance.open()

def close_vocab_reader():
    global _vocab_reader_instance
    if _vocab_reader_instance is not None:
        _vocab_reader_instance.hide()
