
import os

def patch_app_py():
    target_file = "app.py"
    if not os.path.exists(target_file):
        print("Không tìm thấy file app.py")
        return

    with open(target_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    backup_path = target_file + ".bak"
    os.rename(target_file, backup_path)

    new_lines = []
    inserted_import = False
    inserted_global = False
    inserted_checkbox = False
    modified_save_settings = False

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Insert import after 'import os'
        if not inserted_import and "import os" in stripped:
            new_lines.append(line)
            new_lines.append("from path_startup import add_to_startup, remove_from_startup  # Consolog: Auto-start\n")
            inserted_import = True
            continue

        # Insert global variable after "GITHUB_REPO"
        if not inserted_global and "GITHUB_REPO" in stripped:
            new_lines.append(line)
            new_lines.append("AUTO_START_ENABLED = True  # Mặc định bật khởi động cùng Windows\n")
            inserted_global = True
            continue

        # Add checkbox UI in open_settings()
        if not inserted_checkbox and "chatgpt_key_entry.pack" in stripped:
            new_lines.append(line)
            new_lines.append("    auto_start_var = tk.BooleanVar(value=AUTO_START_ENABLED)\n")
            new_lines.append("    auto_start_checkbox = tk.Checkbutton(popup, text=\"Khởi động cùng Windows\", variable=auto_start_var)\n")
            new_lines.append("    auto_start_checkbox.pack(pady=5)\n")
            inserted_checkbox = True
            continue

        # Replace save_settings() logic
        if not modified_save_settings and "def save_settings():" in stripped:
            new_lines.append(line)  # def save_settings():
            new_lines.extend([
                "    global arrange_width, arrange_height, CHATGPT_API_KEY, DEFAULT_TARGET_LANG, AUTO_START_ENABLED\n",
                "    try:\n",
                "        w = int(entry_width.get())\n",
                "        h = int(entry_height.get())\n",
                "        arrange_width = w\n",
                "        arrange_height = h\n",
                "        save_chatgpt_api_key(chatgpt_key_entry.get().strip())\n",
                "        CHATGPT_API_KEY = chatgpt_key_entry.get().strip()\n",
                "        DEFAULT_TARGET_LANG = translation_lang_var.get()\n",
                "        AUTO_START_ENABLED = auto_start_var.get()\n",
                "        if AUTO_START_ENABLED:\n",
                "            add_to_startup(\"AutoTdataTool\")\n",
                "        else:\n",
                "            remove_from_startup(\"AutoTdataTool\")\n",
                "        messagebox.showinfo(\"Setting\", \"Đã lưu cấu hình thành công!\")\n",
                "        popup.destroy()\n",
                "    except Exception as e:\n",
                "        messagebox.showerror(\"Error\", f\"Giá trị không hợp lệ: {e}\")\n"
            ])
            modified_save_settings = True
            # Skip old body of save_settings
            while i + 1 < len(lines) and "def " not in lines[i+1] and not lines[i+1].strip().startswith("tk.") and lines[i+1].strip() != "":
                i += 1
            continue

        new_lines.append(line)

    with open(target_file, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    print("✅ Đã patch thành công. File gốc được backup thành app.py.bak")

if __name__ == "__main__":
    patch_app_py()
