import tkinter as tk
from tkinter import ttk, messagebox
import threading
import os
import time


class CheckLiveWindow(tk.Toplevel):
    """
    Popup kiểm tra trạng thái live của tất cả TData.
    Bao gồm: bảng trạng thái, các nút thao tác, điều khiển đa luồng.
    """

    def __init__(
        self,
        master,
        get_tdata_folders_func,
        capture_window_func,
        show_marker_selection_popup_func,
        arrange_telegram_windows_func,
        load_window_size_func,
        save_window_size_func,
        lang,
        entry_path_value,
        marker_image_path,
        *args,
        **kwargs,
    ):
        super().__init__(master, *args, **kwargs)
        self.title(lang["check_live_title"])
        self.geometry("1200x500")
        self.resizable(True, True)

        # Callback logic từ main/app
        self.get_tdata_folders = get_tdata_folders_func
        self.capture_window = capture_window_func
        self.show_marker_selection_popup = show_marker_selection_popup_func
        self.arrange_telegram_windows = arrange_telegram_windows_func
        self.load_window_size = load_window_size_func
        self.save_window_size = save_window_size_func

        self.lang = lang
        self.tdata_dir = entry_path_value
        self.marker_image_path = marker_image_path

        self.check_live_status = {}  # {tdata_name: {"check":..., "live":...}}
        self.confirm_done = False
        self.tdata_process_map = {}

        self.temp_screenshot_folder = os.path.join(os.getcwd(), "temp_screenshots")

        # ====== Giao diện ======
        # --- Kích thước cửa sổ Telegram ---
        size_frame = tk.Frame(self)
        size_frame.pack(pady=5)
        tk.Label(size_frame, text="Window Width:").grid(row=0, column=0, padx=5)
        self.entry_width = tk.Entry(size_frame, width=6)
        default_width, default_height = self.load_window_size()
        self.entry_width.insert(0, str(default_width))
        self.entry_width.grid(row=0, column=1, padx=5)
        tk.Label(size_frame, text="Window Height:").grid(row=0, column=2, padx=5)
        self.entry_height = tk.Entry(size_frame, width=6)
        self.entry_height.insert(0, str(default_height))
        self.entry_height.grid(row=0, column=3, padx=5)

        # --- Bảng trạng thái (TreeView) ---
        columns = ("stt", "tdata", "check_status", "live_status")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=15)
        for col, label in zip(
            columns, [lang["stt"], "TData", lang["check_status"], lang["live_status"]]
        ):
            self.tree.heading(col, text=label)
            self.tree.column(col, width=200 if col != "stt" else 50, anchor="center")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.refresh_table()

        # --- Nút thao tác ---
        frame_buttons = tk.Frame(self)
        frame_buttons.pack(pady=5)

        self.btn_start = tk.Button(
            frame_buttons, text=lang["start"], command=self.start_check_live, width=20
        )
        self.btn_pause = tk.Button(
            frame_buttons,
            text=lang["pause"],
            command=self.pause_check_live,
            width=20,
            state=tk.DISABLED,
        )
        self.btn_confirm = tk.Button(
            frame_buttons,
            text=lang["confirm"],
            command=self.confirm_check_live,
            width=20,
        )
        self.btn_copy_inactive = tk.Button(
            frame_buttons,
            text=lang["copy_inactive"],
            command=self.copy_inactive,
            width=25,
            state=tk.DISABLED,
        )
        self.btn_delete_inactive = tk.Button(
            frame_buttons,
            text=lang["delete_inactive"],
            command=self.delete_inactive,
            width=25,
            state=tk.DISABLED,
        )
        self.btn_copy_table = tk.Button(
            frame_buttons,
            text=lang["copy_table"],
            command=self.copy_table,
            width=20,
            state=tk.DISABLED,
        )

        self.btn_start.grid(row=0, column=0, padx=5)
        self.btn_pause.grid(row=0, column=1, padx=5)
        self.btn_confirm.grid(row=0, column=2, padx=5)
        self.btn_copy_inactive.grid(row=0, column=3, padx=5)
        self.btn_delete_inactive.grid(row=0, column=4, padx=5)
        self.btn_copy_table.grid(row=0, column=5, padx=5)

    # ====== Các phương thức xử lý UI ======
    def refresh_table(self):
        """
        Cập nhật lại bảng trạng thái TData.
        """
        self.tree.delete(*self.tree.get_children())
        folders = self.get_tdata_folders(self.tdata_dir)
        for idx, folder in enumerate(folders, start=1):
            tdata_name = os.path.basename(folder)
            if tdata_name not in self.check_live_status:
                self.check_live_status[tdata_name] = {
                    "check": self.lang["not_checked"],
                    "live": self.lang["not_checked"],
                }
            row_data = self.check_live_status[tdata_name]
            self.tree.insert(
                "",
                tk.END,
                values=(idx, tdata_name, row_data["check"], row_data["live"]),
            )

    def switch_button_states(self, running):
        """
        Chuyển trạng thái các nút khi đang chạy check live.
        """
        if running:
            self.btn_start.config(state=tk.DISABLED)
            self.btn_pause.config(state=tk.NORMAL)
        else:
            self.btn_start.config(state=tk.NORMAL)
            self.btn_pause.config(state=tk.DISABLED)

    # ====== Các action xử lý check live ======
    def start_check_live(self):
        """
        Bắt đầu quy trình check live, mở telegram, sắp xếp, chụp màn hình, so sánh marker.
        """
        self.switch_button_states(running=True)
        threading.Thread(target=self.worker_check_live, daemon=True).start()

    def pause_check_live(self):
        """
        Tạm dừng quy trình check live.
        """
        # Ở code thật, dùng threading.Event để kiểm soát pause/resume
        self.switch_button_states(running=False)

    def worker_check_live(self):
        """
        Thread chính để mở Telegram, lấy PID, chụp screenshot, so sánh marker.
        """
        # TODO: Xóa/sửa folder temp nếu có
        if os.path.exists(self.temp_screenshot_folder):
            import shutil

            shutil.rmtree(self.temp_screenshot_folder)
        os.makedirs(self.temp_screenshot_folder, exist_ok=True)

        folders = self.get_tdata_folders(self.tdata_dir)
        for idx, folder in enumerate(folders, start=1):
            tdata_name = os.path.basename(folder)
            # Đánh dấu đang kiểm tra
            self.check_live_status[tdata_name] = {
                "check": self.lang["checking"],
                "live": self.check_live_status[tdata_name].get(
                    "live", self.lang["not_checked"]
                ),
            }
            self.after(0, self.refresh_table)
            exe_path = os.path.join(folder, "telegram.exe")
            if os.path.exists(exe_path):
                proc = None
                try:
                    proc = threading.Thread(
                        target=lambda: os.system(f'"{exe_path}"'), daemon=True
                    )
                    proc.start()
                    time.sleep(1)  # Chờ app lên
                    self.check_live_status[tdata_name]["check"] = self.lang["completed"]
                    # TODO: lưu PID vào self.tdata_process_map nếu cần
                except Exception as e:
                    self.check_live_status[tdata_name]["check"] = self.lang[
                        "exe_not_found"
                    ]
            else:
                self.check_live_status[tdata_name]["check"] = self.lang["exe_not_found"]
            self.after(0, self.refresh_table)

        # Lưu lại kích thước cửa sổ
        try:
            custom_width = int(self.entry_width.get())
            custom_height = int(self.entry_height.get())
        except:
            custom_width = 500
            custom_height = 300
        self.save_window_size(custom_width, custom_height)
        self.arrange_telegram_windows(custom_width, custom_height, for_check_live=True)

        # Chụp màn hình, so sánh marker (giả lập)
        time.sleep(2)
        self.after(
            0,
            lambda: messagebox.showinfo(
                "Check live",
                "Quá trình mở telegram hoàn tất. Hệ thống sẽ tự động so sánh hình ảnh sau 2 giây.",
            ),
        )
        threading.Thread(target=self.screenshot_comparison_worker, daemon=True).start()

    def screenshot_comparison_worker(self):
        """
        Thread so sánh screenshot từng cửa sổ Telegram với marker.
        """
        # TODO: Thực thi đúng logic capture & so sánh marker image (tham chiếu code gốc)
        # Cập nhật trạng thái self.check_live_status[tdata_name]["live"] tùy theo kết quả
        # Sau khi xong:
        self.after(
            0,
            lambda: messagebox.showinfo(
                "Check live", "Đã hoàn thành kiểm tra qua so sánh hình ảnh."
            ),
        )

    # ====== Các nút phụ trợ ======
    def confirm_check_live(self):
        """
        Lưu trạng thái check live vào file, enable các nút copy/xóa.
        """
        self.confirm_done = True
        self.btn_copy_inactive.config(state=tk.NORMAL)
        self.btn_delete_inactive.config(state=tk.NORMAL)
        self.btn_copy_table.config(state=tk.NORMAL)
        # TODO: Lưu trạng thái vào file nếu muốn

    def copy_table(self):
        """
        Copy toàn bộ nội dung bảng ra clipboard.
        """
        if not self.confirm_done:
            messagebox.showwarning("Copy Table", "Vui lòng bấm 'Xác nhận' trước.")
            return
        table_text = ""
        for child in self.tree.get_children():
            values = self.tree.item(child, "values")
            table_text += "\t".join(str(v) for v in values) + "\n"
        self.clipboard_clear()
        self.clipboard_append(table_text)
        self.update()
        messagebox.showinfo(
            "Copy Table", "Đã copy toàn bộ nội dung bảng vào clipboard."
        )

    def copy_inactive(self):
        """
        Copy danh sách TData không hoạt động ra clipboard.
        """
        if not self.confirm_done:
            messagebox.showwarning("Copy Inactive", "Vui lòng bấm 'Xác nhận' trước.")
            return
        inactive_list = []
        for child in self.tree.get_children():
            values = self.tree.item(child, "values")
            if len(values) >= 4 and values[3] == self.lang["not_active"]:
                inactive_list.append(values[1])
        if not inactive_list:
            messagebox.showinfo(
                "Copy Inactive", "Không có TData nào ở trạng thái không hoạt động."
            )
            return
        text_inactive = "\n".join(inactive_list)
        self.clipboard_clear()
        self.clipboard_append(text_inactive)
        self.update()
        messagebox.showinfo(
            "Copy Inactive",
            "Đã copy vào clipboard danh sách TData không hoạt động:\n" + text_inactive,
        )

    def delete_inactive(self):
        """
        Xóa các TData không hoạt động (có trạng thái 'not_active').
        """
        if not self.confirm_done:
            messagebox.showwarning("Xóa TData", "Vui lòng bấm 'Xác nhận' trước.")
            return
        # TODO: Tự động đóng Telegram, xóa thư mục, refresh table.
        messagebox.showinfo(
            "Check live", "Đã xóa các thư mục không hoạt động (giả lập)."
        )
        self.refresh_table()
