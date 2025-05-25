import tkinter as tk
from ui.component.path_selector import PathSelectorFrame
from ui.component.stats_panel import StatsPanel
from ui.component.log_panel import LogPanel
# Bạn sẽ import thêm các component khác khi làm tiếp bên dưới

class MainWindow(tk.Tk):
    """
    Giao diện chính của ứng dụng. Chứa các phần chính:
    - Tiêu đề
    - Frame chọn đường dẫn
    - Các nút chức năng chính
    - Khu vực thống kê
    - Log/logging panel
    """
    def __init__(self, lang, version_info, on_login_all, on_check_live, on_settings, on_update, on_autoit, on_arrange, on_close, on_open_telegram, on_copy_telegram):
        super().__init__()
        self.title(lang["title"])
        self.geometry("650x800")

        # Label tiêu đề
        tk.Label(self, text=lang["title"], font=("Arial Unicode MS", 14, "bold")).pack(pady=10)

        # Frame chọn đường dẫn (reusable component)
        self.path_selector = PathSelectorFrame(self, lang)
        self.path_selector.pack(pady=5)

        # Các nút chức năng chính
        frame_buttons = tk.Frame(self)
        frame_buttons.pack(pady=5)

        btn_login_all = tk.Button(frame_buttons, text=lang["login_all"], command=on_login_all, width=18)
        btn_check_live = tk.Button(frame_buttons, text=lang["check_live"], command=on_check_live, width=18)
        btn_setting = tk.Button(frame_buttons, text="⚙️ Setting", command=on_settings, width=18)
        btn_update = tk.Button(frame_buttons, text=lang["check_update"], command=on_update, width=18)
        btn_auto_it = tk.Button(frame_buttons, text=lang["auto_it"], command=on_autoit, width=18)
        btn_arrange = tk.Button(frame_buttons, text=lang["arrange_telegram"], command=on_arrange, width=18)
        btn_close = tk.Button(frame_buttons, text=lang["close_telegram"], command=on_close, width=18)
        btn_open = tk.Button(frame_buttons, text=lang["open_telegram"], command=on_open_telegram, width=18)
        btn_copy = tk.Button(frame_buttons, text=lang["copy_telegram"], command=on_copy_telegram, width=18)

        # Sắp xếp nút dạng lưới cho gọn
        btn_login_all.grid(row=0, column=0, padx=5, pady=5)
        btn_check_live.grid(row=0, column=1, padx=5, pady=5)
        btn_setting.grid(row=0, column=2, padx=5, pady=5)
        btn_update.grid(row=1, column=0, padx=5, pady=5)
        btn_auto_it.grid(row=1, column=1, padx=5, pady=5)
        btn_arrange.grid(row=1, column=2, padx=5, pady=5)
        btn_close.grid(row=2, column=0, padx=5, pady=5)
        btn_open.grid(row=2, column=1, padx=5, pady=5)
        btn_copy.grid(row=2, column=2, padx=5, pady=5)

        # Khu vực thống kê
        self.stats_panel = StatsPanel(self, lang)
        self.stats_panel.pack(pady=10)

        # Khu vực log
        self.log_panel = LogPanel(self, lang)
        self.log_panel.pack(pady=10)

        # Footer version
        footer = tk.Label(self, text=version_info, font=("Arial Unicode MS", 8))
        footer.pack(side="bottom", fill="x", pady=5)
