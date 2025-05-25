import tkinter as tk
import os

# Import các component đã chuẩn hóa
from component.path_selector import PathSelector
from component.stats_panel import StatsPanel
from component.log_panel import LogPanel

from settings_window import SettingsWindow
from login_window import LoginWindow
from check_live_window import CheckLiveWindow

# Import các hàm tiện ích/logic ngoài (có thể nằm trong resources.utils hoặc module riêng)
# from resources.utils import ... # Tùy bạn tách ra đâu, ở đây tôi ví dụ luôn các hàm update_stats, update_logged v.v


class MainWindow(tk.Tk):
    """
    MainWindow: cửa sổ chính, nơi kết nối toàn bộ component, quản lý callback, wiring UI.
    """

    def __init__(self, lang, config_files):
        super().__init__()
        self.title(lang["title"])
        self.geometry("650x800")
        self.resizable(False, False)

        self.lang = lang
        # ---- Biến config truyền cho component ----
        self.config_file = config_files.get("main", "config.txt")
        self.window_size_file = config_files.get("window_size", "window_size.txt")
        self.marker_image_path = config_files.get("marker_image", "marker_image.png")

        # ---- Biến trạng thái app (có thể mở rộng) ----
        self.arrange_width = 500
        self.arrange_height = 504
        self.chatgpt_api_key = ""
        self.default_target_lang = "vi"

        # ---- 1. Path Selector Panel ----
        self.path_selector = PathSelector(
            self,
            lang=self.lang,
            config_file=self.config_file,
            on_path_change=self.on_path_change,
        )
        self.path_selector.pack(pady=5, fill=tk.X)

        # ---- 2. Stats Panel ----
        self.stats_panel = StatsPanel(self, lang=self.lang)
        self.stats_panel.pack(pady=5, fill=tk.X)

        # ---- 3. Log Panel ----
        self.log_panel = LogPanel(self, lang=self.lang)
        self.log_panel.pack(pady=5, fill=tk.X)

        # ---- 4. Dãy nút chức năng chính (login, check live, setting...) ----
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)
        tk.Button(
            btn_frame,
            text=self.lang["login_all"],
            command=self.open_login_window,
            width=18,
        ).grid(row=0, column=0, padx=5, pady=5)
        tk.Button(
            btn_frame,
            text=self.lang["check_live"],
            command=self.open_check_live_window,
            width=18,
        ).grid(row=0, column=1, padx=5, pady=5)
        tk.Button(
            btn_frame, text="⚙️ Setting", command=self.open_settings_window, width=18
        ).grid(row=0, column=2, padx=5, pady=5)

        # ---- Footer phiên bản, bản quyền... ----
        self.footer = tk.Label(
            self, text="Version 1.0.0 - Developed by You", font=("Arial Unicode MS", 8)
        )
        self.footer.pack(side="bottom", fill="x", pady=5)

        # ---- Auto cập nhật stats/log lần đầu ----
        self.on_path_change(self.path_selector.get_path())

        # ---- Sự kiện đóng cửa sổ ----
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    # =================== CALLBACK VÀ LOGIC CHÍNH ===================
    def on_path_change(self, folder_path):
        """
        Callback mỗi khi path đổi (từ PathSelector), update stats, log...
        """
        # ---- Update stats panel ----
        info_text = self.generate_stats_text(folder_path)
        self.stats_panel.update_stats(info_text)
        # ---- Log lại sự kiện ----
        self.log_panel.add_log(f"Consolog: Đã chọn folder: {folder_path}")

    def generate_stats_text(self, folder_path):
        """
        Duyệt thư mục, trả về chuỗi thống kê để hiển thị lên stats panel.
        """
        info_list = []
        if not folder_path or not os.path.exists(folder_path):
            return "Không tìm thấy thư mục, vui lòng chọn lại."
        try:
            subfolders = [
                d
                for d in os.listdir(folder_path)
                if os.path.isdir(os.path.join(folder_path, d))
            ]
        except Exception as e:
            return f"Không thể đọc thư mục: {e}"
        for sub in subfolders:
            sub_path = os.path.join(folder_path, sub)
            tdata_count = sum(
                1
                for item in os.listdir(sub_path)
                if item.lower() == "tdata"
                and os.path.isdir(os.path.join(sub_path, item))
            )
            info_list.append(f"- {sub}: có {tdata_count} tdata folder(s)")
        return "\n".join(info_list) if info_list else "Không có thư mục con nào."

    def open_login_window(self):
        """
        Mở popup đăng nhập hàng loạt tài khoản.
        """
        LoginWindow(
            self,
            get_tdata_folders_func=self.get_tdata_folders,
            login_account_func=self.login_account,
            open_telethon_terminal_func=self.open_telethon_terminal,
            update_privacy_func=self.update_privacy,
            delete_all_sessions_func=self.delete_all_sessions,
            lang=self.lang,
            entry_path_value=self.path_selector.get_path(),
        )

    def open_check_live_window(self):
        """
        Mở popup check live các tdata.
        """
        CheckLiveWindow(
            self,
            get_tdata_folders_func=self.get_tdata_folders,
            capture_window_func=self.capture_window,
            show_marker_selection_popup_func=self.show_marker_selection_popup,
            arrange_telegram_windows_func=self.arrange_telegram_windows,
            load_window_size_func=self.load_window_size,
            save_window_size_func=self.save_window_size,
            lang=self.lang,
            entry_path_value=self.path_selector.get_path(),
            marker_image_path=self.marker_image_path,
        )

    def open_settings_window(self):
        """
        Mở popup cài đặt, nhận giá trị mới về cho MainWindow.
        """

        def save_callback(config):
            self.arrange_width = config["arrange_width"]
            self.arrange_height = config["arrange_height"]
            self.chatgpt_api_key = config["chatgpt_api_key"]
            self.default_target_lang = config["default_target_lang"]
            self.log_panel.add_log(
                f"Consolog: Đã thay đổi cấu hình sắp xếp và API key."
            )

        SettingsWindow(
            self,
            arrange_width=self.arrange_width,
            arrange_height=self.arrange_height,
            chatgpt_api_key=self.chatgpt_api_key,
            default_target_lang=self.default_target_lang,
            on_save_callback=save_callback,
            lang=self.lang,
        )

    def on_closing(self):
        """
        Xử lý khi đóng cửa sổ chính.
        """
        # Có thể thêm logic lưu trạng thái, log, hỏi xác nhận...
        self.log_panel.add_log("Consolog: Đã thoát ứng dụng.")
        self.destroy()

    # =================== CÁC HÀM GIẢ LẬP HOẶC THAM CHIẾU ĐẾN LOGIC GỐC ===================
    # (Bạn cần tự import hoặc wiring từ resources/utils, cores/...)
    def get_tdata_folders(self, folder_path):
        """
        Duyệt thư mục, trả về danh sách các folder tdata (mapping với hàm get_tdata_folders ở code gốc).
        """
        if not folder_path or not os.path.exists(folder_path):
            return []
        subfolders = [
            os.path.join(folder_path, d)
            for d in os.listdir(folder_path)
            if os.path.isdir(os.path.join(folder_path, d))
        ]
        return subfolders

    def login_account(self, folder, update_item_callback):
        """
        Logic đăng nhập tài khoản (mapping với hàm login_account gốc).
        """
        # TODO: wiring tới logic thật sự của bạn!
        self.log_panel.add_log(
            f"Consolog: Login account {os.path.basename(folder)} (giả lập)."
        )
        return True

    def open_telethon_terminal(self, session_path):
        """
        Mở telethon terminal cho session đã chọn.
        """
        self.log_panel.add_log(
            f"Consolog: Open Telethon Terminal for {session_path} (giả lập)."
        )

    def update_privacy(self, session_path):
        """
        Logic update quyền riêng tư (mapping với code gốc).
        """
        self.log_panel.add_log(
            f"Consolog: Update privacy cho {session_path} (giả lập)."
        )

    def delete_all_sessions(self):
        """
        Xóa session không hoạt động.
        """
        self.log_panel.add_log(
            f"Consolog: Đã xóa các session không hoạt động (giả lập)."
        )

    def capture_window(self, window_handle):
        """
        Chụp màn hình cửa sổ Telegram (mapping với capture_window ở checklive/compare.py).
        """
        self.log_panel.add_log(f"Consolog: Capture window {window_handle} (giả lập).")
        return None

    def show_marker_selection_popup(self, screenshot_paths):
        """
        Hiển thị popup chọn marker (mapping với checklive/marker.py).
        """
        self.log_panel.add_log(f"Consolog: Show marker selection popup (giả lập).")

    def arrange_telegram_windows(self, width, height, for_check_live=False):
        """
        Sắp xếp cửa sổ Telegram kiểu lưới/cascade.
        """
        self.log_panel.add_log(
            f"Consolog: Arrange Telegram windows: {width}x{height}, check_live={for_check_live}"
        )

    def load_window_size(self):
        """
        Đọc kích thước cửa sổ từ file (window_size.txt hoặc tương tự).
        """
        if os.path.exists(self.window_size_file):
            try:
                with open(self.window_size_file, "r", encoding="utf-8") as f:
                    line = f.read().strip().split(",")
                    return int(line[0]), int(line[1])
            except:
                pass
        return 500, 504

    def save_window_size(self, width, height):
        """
        Lưu kích thước cửa sổ vào file.
        """
        with open(self.window_size_file, "w", encoding="utf-8") as f:
            f.write(f"{width},{height}")


# ======= CHẠY APP ==========
if __name__ == "__main__":
    # Giả lập lang và config cho chạy thử
    lang = {
        "title": "Telegram TData Tool",
        "login_all": "Đăng nhập tất cả",
        "check_live": "Check live",
        "stats_label": "Thống kê TData",
        "log_label": "Log",
        "choose_folder": "Chọn thư mục",
        "save_path": "Lưu đường dẫn",
        "msg_saved_path": "Đã lưu đường dẫn thành công!",
        "msg_error_path": "Đường dẫn không hợp lệ!",
    }
    config_files = {
        "main": "config.txt",
        "window_size": "window_size.txt",
        "marker_image": "marker_image.png",
    }
    app = MainWindow(lang, config_files)
    app.mainloop()
