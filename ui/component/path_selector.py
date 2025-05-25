import tkinter as tk
from tkinter import filedialog, messagebox
import os


class PathSelector(tk.Frame):
    """
    Panel chọn và lưu đường dẫn thư mục chứa các TData.
    - Hiển thị entry để nhập hoặc paste đường dẫn
    - Nút Browse để mở hộp thoại chọn thư mục
    - Nút Save để xác nhận/lưu path
    - Gọi callback khi path đổi (giúp cập nhật stats/log bên ngoài)
    """

    def __init__(
        self,
        parent,
        lang=None,
        config_file="config.txt",
        on_path_change=None,
        *args,
        **kwargs
    ):
        """
        Args:
            parent: Widget cha (MainWindow)
            lang: dict ngôn ngữ đa ngữ (tùy chọn)
            config_file: file lưu path (default: 'config.txt')
            on_path_change: callback truyền path mới mỗi khi lưu thành công
        """
        super().__init__(parent, *args, **kwargs)
        self.lang = lang or {
            "choose_folder": "Chọn thư mục",
            "save_path": "Lưu đường dẫn",
            "msg_saved_path": "Đã lưu đường dẫn thành công!",
            "msg_error_path": "Đường dẫn không hợp lệ!",
        }
        self.config_file = config_file
        self.on_path_change = on_path_change

        # --- Layout UI ---
        self.entry_path = tk.Entry(self, width=50)
        self.entry_path.pack(side=tk.LEFT, padx=5)
        btn_browse = tk.Button(
            self, text=self.lang["choose_folder"], command=self.browse_folder
        )
        btn_browse.pack(side=tk.LEFT)
        btn_save = tk.Button(self, text=self.lang["save_path"], command=self.save_path)
        btn_save.pack(side=tk.LEFT, padx=(5, 0))

        # --- Nếu đã có config, load lên ---
        saved_path = self.load_path()
        if saved_path:
            self.entry_path.insert(0, saved_path)
            if self.on_path_change:
                self.on_path_change(saved_path)

    def browse_folder(self):
        """
        Mở dialog chọn thư mục, điền path vào entry.
        """
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.entry_path.delete(0, tk.END)
            self.entry_path.insert(0, folder_selected)

    def save_path(self):
        """
        Lưu path vào file cấu hình nếu hợp lệ, callback ra ngoài nếu có.
        """
        folder_path = self.entry_path.get().strip()
        if os.path.exists(folder_path):
            with open(self.config_file, "w", encoding="utf-8") as f:
                f.write(folder_path)
            messagebox.showinfo("Lưu thành công", self.lang["msg_saved_path"])
            if self.on_path_change:
                self.on_path_change(folder_path)
        else:
            messagebox.showerror("Lỗi", self.lang["msg_error_path"])

    def load_path(self):
        """
        Đọc path từ file config (nếu có), trả về str.
        """
        if os.path.exists(self.config_file):
            with open(self.config_file, "r", encoding="utf-8") as f:
                return f.read().strip()
        return ""

    def get_path(self):
        """
        Lấy path hiện tại trong entry (dùng cho MainWindow hoặc các panel khác).
        """
        return self.entry_path.get().strip()
