# ui/check_live_window.py

import os
import shutil
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox

# Hàm tạo giao diện Check Live
def create_check_live_window(
    root,
    lang,
    entry_path,                           # tk.Entry chứa đường dẫn tdata
    get_tdata_folders,                    # Hàm trả về list folder tdata
    refresh_logged_callback,              # Callback cập nhật bảng đã đăng nhập
    capture_window,                       # Hàm chụp screenshot cửa sổ
    arrange_telegram_windows,             # Hàm sắp xếp cửa sổ Telegram
    compare_screenshot_with_marker,       # Hàm so sánh ảnh
    show_marker_selection_popup,          # Hàm chọn marker image
    save_check_live_status_file,          # Hàm lưu trạng thái check live ra file
    auto_close_telegram,                  # Hàm đóng tất cả tiến trình Telegram
    send2trash,                           # Hàm gửi folder vào thùng rác
    lang_keys,                            # Các key của lang (để tra nhanh)
    load_window_size,                     # Hàm đọc kích thước cửa sổ
    save_window_size                      # Hàm lưu kích thước cửa sổ
):
    """
    Tạo cửa sổ kiểm tra trạng thái live của các account Telegram (Check Live).

    Các callback/hàm nghiệp vụ đều được truyền vào để dễ unit test và mở rộng.
    """

    cl_win = tk.Toplevel(root)
    cl_win.title(lang["check_live_title"])
    cl_win.geometry("1200x500")

    # Frame nhập kích thước cửa sổ Telegram để check
    size_frame = tk.Frame(cl_win)
    size_frame.pack(pady=5)

    tk.Label(size_frame, text="Window Width:").grid(row=0, column=0, padx=5)
    entry_width = tk.Entry(size_frame, width=6)
    default_width, default_height = load_window_size()
    entry_width.insert(0, str(default_width))
    entry_width.grid(row=0, column=1, padx=5)

    tk.Label(size_frame, text="Window Height:").grid(row=0, column=2, padx=5)
    entry_height = tk.Entry(size_frame, width=6)
    entry_height.insert(0, str(default_height))
    entry_height.grid(row=0, column=3, padx=5)

    # Bảng trạng thái các tdata
    columns = ("stt", "tdata", "check_status", "live_status")
    tree = ttk.Treeview(cl_win, columns=columns, show="headings", height=15)
    tree.heading("stt", text=lang_keys["stt"])
    tree.heading("tdata", text="TData")
    tree.heading("check_status", text=lang_keys["check_status"])
    tree.heading("live_status", text=lang_keys["live_status"])
    for col, w in zip(columns, (50, 200, 200, 200)):
        tree.column(col, width=w, anchor="center")
    tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Biến lưu trạng thái
    check_live_status = {}
    confirm_done = [False]  # Dùng list để có thể modify trong scope nested func
    TEMP_SCREENSHOT_FOLDER = [None]        # Cũng vậy

    # Hàm cập nhật bảng trạng thái
    def refresh_table():
        tree.delete(*tree.get_children())
        tdata_dir = entry_path.get()
        folders = get_tdata_folders(tdata_dir)
        for idx, folder in enumerate(folders, start=1):
            tdata_name = os.path.basename(folder)
            if tdata_name not in check_live_status:
                check_live_status[tdata_name] = {
                    "check": lang_keys["not_checked"],
                    "live": lang_keys["not_checked"]
                }
            row_data = check_live_status[tdata_name]
            tree.insert("", tk.END, values=(idx, tdata_name, row_data["check"], row_data["live"]))

    refresh_table_global = refresh_table
    refresh_table()

    # Các hàm start/pause/confirm/copy/delete
    def switch_button_states(running):
        btn_start.config(state=tk.DISABLED if running else tk.NORMAL)
        btn_pause.config(state=tk.NORMAL if running else tk.DISABLED)

    check_live_pause_event = threading.Event()
    check_live_thread = [None]

    def start_check_live():
        # Bắt đầu thread check live
        tdata_process_map = {}
        TEMP_SCREENSHOT_FOLDER[0] = os.path.join(os.getcwd(), "temp_screenshots")
        if os.path.exists(TEMP_SCREENSHOT_FOLDER[0]):
            shutil.rmtree(TEMP_SCREENSHOT_FOLDER[0])
        os.makedirs(TEMP_SCREENSHOT_FOLDER[0], exist_ok=True)

        if check_live_thread[0] and check_live_pause_event.is_set():
            check_live_pause_event.clear()
            switch_button_states(True)
            return

        switch_button_states(True)

        def worker():
            tdata_dir = entry_path.get()
            folders = get_tdata_folders(tdata_dir)

            # 1. Mở Telegram, gán PID cho từng folder
            for folder in folders:
                while check_live_pause_event.is_set():
                    time.sleep(0.3)
                tdata_name = os.path.basename(folder)
                check_live_status[tdata_name] = {
                    "check": lang_keys["checking"],
                    "live": check_live_status[tdata_name].get("live", lang_keys["not_checked"])
                }
                cl_win.after(0, refresh_table_global)

                exe_path = os.path.join(folder, "telegram.exe")
                if os.path.exists(exe_path):
                    proc = __import__("subprocess").Popen([exe_path])
                    pid = proc.pid
                    tdata_process_map.setdefault(tdata_name, []).append(pid)
                    time.sleep(1)
                    check_live_status[tdata_name]["check"] = lang_keys["completed"]
                else:
                    check_live_status[tdata_name]["check"] = lang_keys["exe_not_found"]

                cl_win.after(0, refresh_table_global)

            # 2. Sắp xếp cửa sổ
            try:
                custom_width = int(entry_width.get())
            except:
                custom_width = 500
            try:
                custom_height = int(entry_height.get())
            except:
                custom_height = 300
            save_window_size(custom_width, custom_height)
            arrange_telegram_windows(custom_width, custom_height, for_check_live=True)

            cl_win.after(0, lambda: messagebox.showinfo(
                "Check live",
                "Quá trình mở telegram hoàn tất.\nHệ thống sẽ tự động so sánh hình ảnh sau 2 giây."
            ))

            # 3. Thread so sánh screenshot với marker (phải truyền hàm vào, có thể custom lại)
            def screenshot_comparison_worker():
                time.sleep(2)
                captured_screenshots = {}

                # Chụp screenshot
                for tdata_name, pid_list in tdata_process_map.items():
                    hwnd = None
                    for pid in pid_list:
                        hwnd = get_window_handle_by_pid(pid)  # Hàm này bạn truyền vào nếu muốn
                        if hwnd:
                            break
                    if hwnd:
                        screenshot = capture_window(hwnd)
                        if screenshot:
                            if TEMP_SCREENSHOT_FOLDER[0]:
                                file_path = os.path.join(TEMP_SCREENSHOT_FOLDER[0], f"{tdata_name}_screenshot.png")
                                screenshot.save(file_path)
                                captured_screenshots[tdata_name] = file_path

                # Popup chọn marker nếu có
                if captured_screenshots:
                    show_marker_selection_popup(list(captured_screenshots.values()))

                # So sánh từng ảnh với marker
                marker_image = None
                if os.path.exists("marker_image.png"):
                    from PIL import Image
                    marker_image = Image.open("marker_image.png")

                for tdata_name, file_path in captured_screenshots.items():
                    if marker_image:
                        screenshot = __import__("PIL.Image").open(file_path)
                        is_similar = compare_screenshot_with_marker(screenshot, marker_image)
                        if is_similar:
                            check_live_status[tdata_name]["live"] = lang_keys["not_active"]
                        else:
                            check_live_status[tdata_name]["live"] = lang_keys["live"]
                    else:
                        check_live_status[tdata_name]["live"] = lang_keys["live"]
                    cl_win.after(0, refresh_table_global)

                cl_win.after(0, lambda: messagebox.showinfo("Check live", "Đã hoàn thành kiểm tra qua so sánh hình ảnh."))

            threading.Thread(target=screenshot_comparison_worker, daemon=True).start()
            check_live_thread[0] = None

        check_live_thread[0] = threading.Thread(target=worker, daemon=True)
        check_live_thread[0].start()

    def pause_check_live():
        check_live_pause_event.set()
        switch_button_states(False)

    def confirm_check_live():
        save_check_live_status_file()
        messagebox.showinfo("Check live", f"Đã lưu trạng thái check live vào file check_live_status.txt")
        confirm_done[0] = True
        btn_copy_inactive.config(state=tk.NORMAL)
        btn_delete_inactive.config(state=tk.NORMAL)
        btn_copy_table.config(state=tk.NORMAL)
        # Xóa folder tạm
        if TEMP_SCREENSHOT_FOLDER[0] and os.path.exists(TEMP_SCREENSHOT_FOLDER[0]):
            shutil.rmtree(TEMP_SCREENSHOT_FOLDER[0])
            TEMP_SCREENSHOT_FOLDER[0] = None

    def copy_table():
        if not confirm_done[0]:
            messagebox.showwarning("Copy Table", "Vui lòng bấm 'Xác nhận' trước.")
            return
        table_text = ""
        for child in tree.get_children():
            values = tree.item(child, "values")
            table_text += "\t".join(str(v) for v in values) + "\n"
        root.clipboard_clear()
        root.clipboard_append(table_text)
        root.update()
        messagebox.showinfo("Copy Table", "Đã copy toàn bộ nội dung bảng vào clipboard.")

    def copy_inactive():
        if not confirm_done[0]:
            messagebox.showwarning("Copy Inactive", "Vui lòng bấm 'Xác nhận' trước.")
            return
        inactive_list = []
        for child in tree.get_children():
            values = tree.item(child, "values")
            if len(values) >= 4 and values[3] == lang_keys["not_active"]:
                inactive_list.append(values[1])
        if not inactive_list:
            messagebox.showinfo("Copy Inactive", "Không có TData nào ở trạng thái không hoạt động.")
            return
        text_inactive = "\n".join(inactive_list)
        root.clipboard_clear()
        root.clipboard_append(text_inactive)
        root.update()
        messagebox.showinfo("Copy Inactive", "Đã copy vào clipboard danh sách TData không hoạt động:\n" + text_inactive)

    def delete_inactive():
        if not confirm_done[0]:
            messagebox.showwarning("Xóa TData", "Vui lòng bấm 'Xác nhận' trước.")
            return
        auto_close_telegram()
        tdata_dir = entry_path.get()
        folders = get_tdata_folders(tdata_dir)
        deleted = []
        for folder in folders:
            tdata_name = os.path.basename(folder)
            if check_live_status.get(tdata_name, {}).get("live") == lang_keys["not_active"]:
                if os.path.exists(folder):
                    try:
                        if send2trash:
                            send2trash(folder)
                        else:
                            shutil.rmtree(folder)
                        deleted.append(tdata_name)
                        check_live_status.pop(tdata_name, None)
                    except Exception as e:
                        print(f"ERROR: {e}")
        refresh_table_global()
        messagebox.showinfo("Check live", f"Đã xóa {len(deleted)} thư mục không hoạt động:\n" + ", ".join(deleted))
        save_check_live_status_file()

    # Buttons nhóm chức năng
    frame_buttons = tk.Frame(cl_win)
    frame_buttons.pack(pady=5)

    btn_start = tk.Button(frame_buttons, text=lang_keys["start"], command=start_check_live, width=20)
    btn_pause = tk.Button(frame_buttons, text=lang_keys["pause"], command=pause_check_live, width=20, state=tk.DISABLED)
    btn_confirm = tk.Button(frame_buttons, text=lang_keys["confirm"], command=confirm_check_live, width=20)
    btn_copy_inactive = tk.Button(frame_buttons, text=lang_keys["copy_inactive"], command=copy_inactive, width=25, state=tk.DISABLED)
    btn_delete_inactive = tk.Button(frame_buttons, text=lang_keys["delete_inactive"], command=delete_inactive, width=25, state=tk.DISABLED)
    btn_copy_table = tk.Button(frame_buttons, text=lang_keys["copy_table"], command=copy_table, width=20, state=tk.DISABLED)

    btn_start.grid(row=0, column=0, padx=5)
    btn_pause.grid(row=0, column=1, padx=5)
    btn_confirm.grid(row=0, column=2, padx=5)
    btn_copy_inactive.grid(row=0, column=3, padx=5)
    btn_delete_inactive.grid(row=0, column=4, padx=5)
    btn_copy_table.grid(row=0, column=5, padx=5)

    # Trả về window
    return cl_win

# ---------
# Bạn cần truyền đầy đủ callback business logic và các biến cần thiết khi gọi hàm này từ app.py.
# ---------
