# ui/main_window.py

import tkinter as tk
from tkinter import ttk

def create_main_window(
    root, lang, VERSION_INFO,
    on_browse_folder, on_save_path, on_login_all, on_copy, on_open, on_close,
    on_arrange, on_autoit, on_check_live, on_setting, on_update,
    entry_path, telegram_path_entry,
    update_stats, update_logged,
    text_stats, text_logged, text_log
):
    """
    Tạo và setup giao diện màn hình chính.
    Các tham số là các callback/hàm/biến được truyền từ app.py vào.

    :param root: Tk() root window
    :param lang: dict ngôn ngữ
    :param VERSION_INFO: string version
    ... (các callback khác)
    """
    root.title(lang["title"])

    # Title
    label_title = tk.Label(root, text=lang["title"], font=("Arial Unicode MS", 14, "bold"))
    label_title.pack(pady=10)

    # Chọn folder TData
    frame_path = tk.Frame(root)
    frame_path.pack(pady=5)
    entry_path.pack(in_=frame_path, side=tk.LEFT, padx=5)
    btn_browse = tk.Button(frame_path, text=lang["choose_folder"], command=on_browse_folder)
    btn_browse.pack(side=tk.LEFT)

    # Đường dẫn Telegram exe
    frame_telegram_path = tk.Frame(root)
    frame_telegram_path.pack(pady=5)
    tk.Label(frame_telegram_path, text=lang["telegram_path_label"]).pack(side=tk.LEFT, padx=5)
    telegram_path_entry.pack(in_=frame_telegram_path, side=tk.LEFT, padx=5)

    # Nút lưu
    btn_save = tk.Button(root, text=lang["save_path"], command=on_save_path, width=20)
    btn_save.pack(pady=5)

    # Các nút thao tác chính
    frame_buttons = tk.Frame(root)
    frame_buttons.pack(pady=5)
    btn_login_all = tk.Button(frame_buttons, text=lang["login_all"], command=on_login_all, width=18)
    btn_copy = tk.Button(frame_buttons, text=lang["copy_telegram"], command=on_copy, width=18)
    btn_open = tk.Button(frame_buttons, text=lang["open_telegram"], command=on_open, width=18)
    btn_close = tk.Button(frame_buttons, text=lang["close_telegram"], command=on_close, width=18)
    btn_arrange = tk.Button(frame_buttons, text=lang["arrange_telegram"], command=on_arrange, width=18)
    btn_autoit = tk.Button(frame_buttons, text=lang["auto_it"], command=on_autoit, width=18)
    btn_check_live = tk.Button(frame_buttons, text=lang["check_live"], command=on_check_live, width=18)
    btn_setting = tk.Button(frame_buttons, text="⚙️ Setting", command=on_setting, width=18)
    btn_update = tk.Button(frame_buttons, text=lang["check_update"], command=on_update, width=18)

    # Gán vào grid (chia dòng/cột)
    btn_login_all.grid(row=0, column=0, padx=5, pady=5)
    btn_copy.grid(row=0, column=1, padx=5, pady=5)
    btn_open.grid(row=0, column=2, padx=5, pady=5)
    btn_close.grid(row=1, column=0, padx=5, pady=5)
    btn_arrange.grid(row=1, column=1, padx=5, pady=5)
    btn_autoit.grid(row=1, column=2, padx=5, pady=5)
    btn_check_live.grid(row=2, column=0, padx=5, pady=5)
    btn_setting.grid(row=2, column=1, padx=5, pady=5)
    btn_update.grid(row=2, column=2, padx=5, pady=5)

    # Thống kê
    frame_stats = tk.Frame(root)
    frame_stats.pack(pady=10)
    label_stats = tk.Label(frame_stats, text=lang["stats_label"])
    label_stats.pack()
    text_stats.pack(in_=frame_stats)
    # Có thể bổ sung các widget khác: text_logged, text_log... (theo nhu cầu của bạn)

    # Footer version
    footer = tk.Label(root, text=VERSION_INFO, font=("Arial Unicode MS", 8))
    footer.pack(side="bottom", fill="x", pady=5)
