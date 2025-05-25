# checklive/marker.py

"""
Module xử lý marker image: Chọn, lưu và đọc marker image dùng cho chức năng check live tài khoản Telegram.
Marker image là ảnh "mẫu" dùng để so sánh xác định tài khoản nào đã chết dựa trên screenshot giao diện Telegram.
"""

import os
import shutil
from tkinter import Toplevel, Label, Frame, Listbox, Button, messagebox
from PIL import Image, ImageTk

def show_marker_selection_popup(screenshot_paths, root, marker_image_path):
    """
    Hiển thị popup cho phép người dùng chọn 1 ảnh trong danh sách screenshot để làm marker.
    Ảnh marker sẽ lưu ở marker_image_path.
    
    Args:
        screenshot_paths (list): Danh sách đường dẫn các screenshot đã chụp.
        root (Tk): Cửa sổ Tkinter chính (parent).
        marker_image_path (str): Đường dẫn lưu marker image (thường là "marker_image.png").
    """
    popup = Toplevel(root)
    popup.title("Chọn marker image")
    popup.geometry("800x600")
    
    # Hướng dẫn
    instruction = Label(
        popup,
        text="Hãy chọn 1 ảnh tiêu biểu đại diện cho tài khoản chết (marker image) từ danh sách bên trái.",
        font=("Arial Unicode MS", 10, "bold"),
        wraplength=780
    )
    instruction.pack(pady=10)

    selected_path = {"path": None}

    frame = Frame(popup)
    frame.pack(fill="both", expand=True, padx=10, pady=10)

    # Listbox hiển thị danh sách file
    listbox = Listbox(frame, width=40)
    listbox.pack(side="left", fill="y", padx=5, pady=5)
    for path in screenshot_paths:
        listbox.insert("end", os.path.basename(path))

    # Label preview ảnh
    preview_label = Label(frame)
    preview_label.pack(side="right", fill="both", expand=True, padx=5, pady=5)

    # Hàm cập nhật preview khi chọn file
    def on_select(event):
        selection = listbox.curselection()
        if selection:
            index = selection[0]
            file_path = screenshot_paths[index]
            selected_path["path"] = file_path
            try:
                img = Image.open(file_path)
                img.thumbnail((400, 400))
                photo = ImageTk.PhotoImage(img)
                preview_label.config(image=photo)
                preview_label.image = photo  # Cần giữ tham chiếu, tránh bị xóa
            except Exception as e:
                print(f"[Marker] Lỗi mở ảnh {file_path}: {e}")

    listbox.bind("<<ListboxSelect>>", on_select)

    # Hàm xử lý khi xác nhận chọn marker
    def on_confirm():
        if not selected_path["path"]:
            messagebox.showwarning("Warning", "Vui lòng chọn một ảnh!")
            return
        # Nếu có marker cũ, xóa trước
        if os.path.exists(marker_image_path):
            try:
                os.remove(marker_image_path)
            except Exception as e:
                print(f"[Marker] Lỗi xóa marker cũ: {e}")
        try:
            shutil.copy(selected_path["path"], marker_image_path)
            messagebox.showinfo("Thành công", f"Đã lưu marker image tại {marker_image_path}")
        except Exception as e:
            print(f"[Marker] Lỗi lưu marker image: {e}")
            messagebox.showerror("Lỗi", f"Lỗi lưu marker image: {e}")
        popup.destroy()

    confirm_button = Button(popup, text="Xác nhận", command=on_confirm)
    confirm_button.pack(pady=10)
    popup.transient(root)
    popup.grab_set()
    root.wait_window(popup)


def load_marker_config(marker_config_file):
    """
    Đọc file cấu hình marker (marker_config.txt) để lấy trạng thái (ví dụ: không hỏi lại người dùng).
    Args:
        marker_config_file (str): Đường dẫn file config marker.
    Returns:
        dict: Ví dụ {'dont_ask': True}
    """
    config = {"dont_ask": False}
    if os.path.exists(marker_config_file):
        try:
            with open(marker_config_file, "r", encoding="utf-8") as f:
                line = f.read().strip()
                if line.lower() == "dont_ask=true":
                    config["dont_ask"] = True
        except Exception as e:
            print(f"[Marker] Lỗi đọc marker config: {e}")
    return config

def save_marker_config(config, marker_config_file):
    """
    Lưu cấu hình marker (marker_config.txt).
    Args:
        config (dict): Ví dụ {'dont_ask': True}
        marker_config_file (str): Đường dẫn file config marker.
    """
    try:
        with open(marker_config_file, "w", encoding="utf-8") as f:
            f.write("dont_ask=true" if config.get("dont_ask") else "dont_ask=false")
    except Exception as e:
        print(f"[Marker] Lỗi ghi marker config: {e}")
