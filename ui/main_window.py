import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont

class MainWindow:
    def __init__(self, root, lang):
        self.root = root
        self.lang = lang
        self.setup_ui()

    def setup_ui(self):
        # Set default font
        default_font = tkFont.nametofont("TkDefaultFont")
        default_font.configure(family="Arial Unicode MS", size=10)
        self.root.option_add("*Font", default_font)

        # Title
        label_title = tk.Label(self.root, text=self.lang["title"], font=("Arial Unicode MS", 14, "bold"))
        label_title.pack(pady=10)

        # Path frame
        self.create_path_frame()
        
        # Telegram path frame
        self.create_telegram_path_frame()
        
        # Button frames
        self.create_button_frames()
        
        # Stats and log frames
        self.create_stats_frame()
        self.create_log_frame()

    def create_path_frame(self):
        frame_path = tk.Frame(self.root)
        frame_path.pack(pady=5)
        
        self.entry_path = tk.Entry(frame_path, width=50)
        self.entry_path.pack(side=tk.LEFT, padx=5)
        
        btn_browse = tk.Button(frame_path, text=self.lang["choose_folder"])
        btn_browse.pack(side=tk.LEFT)

    def create_telegram_path_frame(self):
        frame_telegram_path = tk.Frame(self.root)
        frame_telegram_path.pack(pady=5)
        
        tk.Label(frame_telegram_path, text=self.lang["telegram_path_label"]).pack(side=tk.LEFT, padx=5)
        self.telegram_path_entry = tk.Entry(frame_telegram_path, width=50)
        self.telegram_path_entry.pack(side=tk.LEFT, padx=5)

    def create_button_frames(self):
        frame_buttons = tk.Frame(self.root)
        frame_buttons.pack(pady=5)
        
        # First row
        btn_login_all = tk.Button(frame_buttons, text=self.lang["login_all"], width=18)
        btn_copy = tk.Button(frame_buttons, text=self.lang["copy_telegram"], width=18)
        btn_open = tk.Button(frame_buttons, text=self.lang["open_telegram"], width=18)
        
        btn_login_all.grid(row=0, column=0, padx=5, pady=5)
        btn_copy.grid(row=0, column=1, padx=5, pady=5)
        btn_open.grid(row=0, column=2, padx=5, pady=5)
        
        # Second row
        btn_close = tk.Button(frame_buttons, text=self.lang["close_telegram"], width=18)
        btn_arrange = tk.Button(frame_buttons, text=self.lang["arrange_telegram"], width=18)
        btn_auto_it = tk.Button(frame_buttons, text=self.lang["auto_it"], width=18)
        
        btn_close.grid(row=1, column=0, padx=5, pady=5)
        btn_arrange.grid(row=1, column=1, padx=5, pady=5)
        btn_auto_it.grid(row=1, column=2, padx=5, pady=5)
        
        # Third row
        btn_check_live = tk.Button(frame_buttons, text=self.lang["check_live"], width=18)
        btn_setting = tk.Button(frame_buttons, text="⚙️ Setting", width=18)
        btn_update = tk.Button(frame_buttons, text=self.lang["check_update"], width=18)
        
        btn_check_live.grid(row=2, column=0, padx=5, pady=5)
        btn_setting.grid(row=2, column=1, padx=5, pady=5)
        btn_update.grid(row=2, column=2, padx=5, pady=5)

    def create_stats_frame(self):
        frame_stats = tk.Frame(self.root)
        frame_stats.pack(pady=10)
        
        label_stats = tk.Label(frame_stats, text=self.lang["stats_label"])
        label_stats.pack()
        
        self.text_stats = tk.Text(frame_stats, width=70, height=10)
        self.text_stats.pack()

    def create_log_frame(self):
        frame_log = tk.Frame(self.root)
        frame_log.pack(pady=10)
        
        label_log = tk.Label(frame_log, text=self.lang["log_label"])
        label_log.pack()
        
        self.text_log = tk.Text(frame_log, width=70, height=10)
        self.text_log.pack() 