import sys
import time
import os
import random
import threading
import win32gui
import win32con
import pyautogui
import win32ui  # Cần thiết cho PrintWindow (debug)

# ------------------ THÊM KHAI BÁO CHO PAUSE/RESUME ------------------
global_pause_event = threading.Event()

def toggle_pause():
    """Hàm thay đổi trạng thái tạm dừng – tiếp tục toàn bộ tool."""
    if global_pause_event.is_set():
        global_pause_event.clear()
        print("Consolog: Tiếp tục chạy")
    else:
        global_pause_event.set()
        print("Consolog: Tạm dừng chạy")

def sleep_with_pause(duration):
    """Thay thế time.sleep() để kiểm tra trạng thái pause."""
    start = time.time()
    while time.time() - start < duration:
        if global_pause_event.is_set():
            print("Consolog: [sleep_with_pause] Đang tạm dừng, chờ tiếp...")
            while global_pause_event.is_set():
                time.sleep(0.1)
            print("Consolog: [sleep_with_pause] Tiếp tục sau khi tạm dừng.")
        time.sleep(0.1)

def pause_if_needed(pause_event):
    """Nếu pause_event được set, chờ cho đến khi clear."""
    if pause_event and pause_event.is_set():
        print("Consolog: [pause_if_needed] Đang tạm dừng, chờ tiếp...")
        while pause_event.is_set():
            time.sleep(0.1)
        print("Consolog: [pause_if_needed] Tiếp tục sau khi tạm dừng.")

# ------------------ KẾT THÚC PHẦN PAUSE/RESUME ------------------

# Cấu hình chọn cách click: True => sử dụng pyautogui.click() (chiếm chuột)
USE_PYAUTOGUI = True

DATA_PROCESS_FILE = "data_process.text"  # File tạm thời dùng chung cho các thao tác

# --- THÊM BIẾN ĐƯỜNG DẪN ẢNH TỪ ĐƯỜNG DẪN CỨNG SANG RELATIVE ---
IMAGE_DIR = os.path.join(os.path.dirname(__file__), "cropped_images")
print(f"Consolog: Đã chuyển sang sử dụng đường dẫn tương đối cho ảnh: {IMAGE_DIR}")
# --------------------------------------------------------------------------

def get_settings():
    """
    Đọc các file cấu hình ở mục "Cài đặt Đường dẫn" và trả về một dictionary chứa:
      - avatar_path: đường dẫn thư mục chứa ảnh avatar
      - name_change_path: đường dẫn file danh sách tên cần đổi
      - phone_path: đường dẫn file số điện thoại cần thêm
      - desc_path: đường dẫn file mô tả tài khoản
      - tdata_path: đường dẫn chứa Tdata (nếu có)
      - welcome_message: tin nhắn chào mặc định
    Nếu file không tồn tại thì giá trị sẽ là None.
    """
    settings = {}
    config_files = {
        "avatar_path": "avatar_path.txt",
        "name_change_path": "name_change_path.txt",
        "phone_path": "phone_path.txt",
        "desc_path": "desc_path.txt",
        "tdata_path": "tdata_path.txt",
        "welcome_message": "welcome_message.txt"
    }
    for key, filename in config_files.items():
        try:
            with open(filename, "r", encoding="utf-8") as f:
                settings[key] = f.read().strip()
        except Exception as e:
            print(f"Consolog: Lỗi đọc file {filename}: {e}")
            settings[key] = None
    return settings

def send_text_via_post(hwnd, text):
    """
    Gửi chuỗi text tới cửa sổ hwnd bằng cách gửi thông điệp WM_CHAR cho từng ký tự,
    sau đó gửi phím Enter bằng pyautogui.press("enter") để đảm bảo tin nhắn được gửi chính xác.
    Các thông điệp ký tự vẫn dùng PostMessage, chỉ thay đổi phần gửi Enter.
    """
    for ch in text:
        win32gui.PostMessage(hwnd, win32con.WM_CHAR, ord(ch), 0)
        sleep_with_pause(0.05)
    print("Consolog: Sử dụng pyautogui.press('enter') để gửi tin nhắn thay vì PostMessage.")
    pyautogui.press("enter")
    print("Consolog: Delay 3s sau khi ấn Enter")
    sleep_with_pause(3)

def click_at_send_message(hwnd, x, y):
    """
    Click tại tọa độ (x, y) của cửa sổ hwnd bằng cách sử dụng SendMessage.
    Phương pháp này đồng bộ và thường không chiếm chuột.
    """
    lParam = (y << 16) | (x & 0xFFFF)
    win32gui.SendMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
    sleep_with_pause(0.05)
    win32gui.SendMessage(hwnd, win32con.WM_LBUTTONUP, 0, lParam)

def click_at_pyautogui(hwnd, x, y):
    """
    Click thật tại tọa độ (x, y) của cửa sổ hwnd bằng pyautogui.
    Chuyển đổi tọa độ từ không gian client sang tọa độ màn hình.
    """
    client_origin = win32gui.ClientToScreen(hwnd, (0, 0))
    screen_x = client_origin[0] + int(x)
    screen_y = client_origin[1] + int(y)
    print(f"Consolog: Chuyển tọa độ client ({x}, {y}) -> tọa độ screen: ({screen_x}, {screen_y})")
    pyautogui.click(screen_x, screen_y)

def click_at(hwnd, x, y):
    """
    Hàm click chung sử dụng phương pháp được cấu hình qua biến USE_PYAUTOGUI.
    """
    if USE_PYAUTOGUI:
        click_at_pyautogui(hwnd, x, y)
    else:
        click_at_send_message(hwnd, x, y)

def send_key(hwnd, vk):
    """
    Gửi thông điệp của một phím (key down/ key up) tới cửa sổ hwnd dựa trên mã phím ảo.
    """
    win32gui.PostMessage(hwnd, win32con.WM_KEYDOWN, vk, 0)
    sleep_with_pause(0.05)
    win32gui.PostMessage(hwnd, win32con.WM_KEYUP, vk, 0)

def send_ctrl_a(hwnd):
    """
    Giả lập tổ hợp Ctrl+A bằng cách gửi thông điệp cho Ctrl và chữ 'A'.
    """
    win32gui.PostMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_CONTROL, 0)
    win32gui.PostMessage(hwnd, win32con.WM_KEYDOWN, ord('A'), 0)
    sleep_with_pause(0.05)
    win32gui.PostMessage(hwnd, win32con.WM_KEYUP, ord('A'), 0)
    win32gui.PostMessage(hwnd, win32con.WM_KEYUP, win32con.VK_CONTROL, 0)

def click_first_conversation_via_post(hwnd):
    """
    Giả sử vị trí của cuộc hội thoại đầu tiên nằm tại tọa độ (50, 150) của không gian client.
    Thực hiện click qua click_at.
    """
    x, y = 50, 150
    click_at(hwnd, x, y)

def convert_screen_to_hwnd(hwnd, x, y):
    """
    Chuyển đổi tọa độ từ không gian screen sang không gian client của cửa sổ hwnd.
    Đảm bảo kết quả trả về luôn không âm bằng cách lấy client origin rồi trừ.
    """
    client_origin = win32gui.ClientToScreen(hwnd, (0, 0))
    client_x = int(x) - client_origin[0]
    client_y = int(y) - client_origin[1]
    print(f"Consolog: Client origin của hwnd {hwnd} là {client_origin}.")
    print(f"Consolog: (Modified) Tọa độ screen ({x}, {y}) => tọa độ client: ({client_x}, {client_y})")
    return (client_x, client_y)

def get_image_coordinates_in_hwnd(hwnd, image_path, confidence=0.8, debug_filename="debug_generic.png"):
    """
    Tìm vị trí của hình ảnh trên screen và chuyển đổi sang tọa độ client của cửa sổ hwnd.
    Giới hạn vùng tìm kiếm chỉ trong vùng client của cửa sổ bằng tham số region.
    Nếu tìm thấy, trả về tuple (client_x, client_y); nếu không, trả về None.
    debug_filename: Tên file dùng để lưu ảnh debug chụp vùng client trước khi dò.
    """
    if not win32gui.IsWindow(hwnd):
        print("Consolog: HWND không hợp lệ.")
        return None

    client_origin = win32gui.ClientToScreen(hwnd, (0, 0))
    client_rect = win32gui.GetClientRect(hwnd)
    width = client_rect[2]
    height = client_rect[3]
    region = (client_origin[0], client_origin[1], width, height)
    print(f"Consolog: Vùng tìm kiếm cho hwnd {hwnd} là: {region}")

    print("Consolog: Delay 2s để đảm bảo ảnh đã hiện đầy đủ.")
    sleep_with_pause(2)

    try:
        debug_screenshot = pyautogui.screenshot(region=region)
        debug_screenshot.save(debug_filename)
        print(f"Consolog: Đã chụp ảnh vùng client và lưu tại: {debug_filename}")
        loc = pyautogui.locateOnScreen(image_path, confidence=confidence, region=region)
    except Exception as e:
        print(f"Consolog: Lỗi locateOnScreen cho hình {image_path}: {e}")
        return None

    if loc:
        screen_x = int(loc.left)
        screen_y = int(loc.top)
        client_point = convert_screen_to_hwnd(hwnd, screen_x, screen_y)
        print(f"Consolog: (Modified) Locate hình {image_path} trả về tọa độ screen ({screen_x}, {screen_y})")
        print(f"Consolog: Sau chuyển đổi, tọa độ client là: {client_point} trong hwnd {hwnd}")
        return client_point
    else:
        print(f"Consolog: Không tìm thấy hình ảnh: {image_path}")
        return None

def image_exists_in_hwnd(hwnd, image_path, confidence=0.8, debug_filename="debug_temp.png", extra_delay=0):
    """
    Kiểm tra sự tồn tại của hình ảnh trong không gian client của cửa sổ hwnd.
    Nếu tồn tại, trả về True; nếu không, trả về False.
    Thêm extra_delay (nếu có) trước khi tiến hành kiểm tra.
    """
    if extra_delay > 0:
        print(f"Consolog: Delay thêm {extra_delay} giây trước khi kiểm tra sự tồn tại của hình {image_path}.")
        sleep_with_pause(extra_delay)
    loc = get_image_coordinates_in_hwnd(hwnd, image_path, confidence=confidence, debug_filename=debug_filename)
    if loc:
        print(f"Consolog: (Modified) Hình ảnh {image_path} tồn tại trong hwnd {hwnd}.")
        return True
    else:
        print(f"Consolog: (Modified) Hình ảnh {image_path} không tồn tại trong hwnd {hwnd}.")
        return False

def check_image_debug(hwnd, image_path, debug_filename, confidence=0.8, extra_delay=0):
    """
    Chụp ảnh vùng client của hwnd và kiểm tra xem image_path có xuất hiện hay không.
    Ảnh chụp sẽ được lưu vào debug_filename.
    Nếu extra_delay > 0, thực hiện delay thêm trước khi chụp.
    """
    if extra_delay > 0:
        print(f"Consolog: Delay thêm {extra_delay} giây trước khi chụp debug image '{debug_filename}'.")
        sleep_with_pause(extra_delay)
    loc = get_image_coordinates_in_hwnd(hwnd, image_path, confidence=confidence, debug_filename=debug_filename)
    if loc:
        print(f"Consolog: Debug image '{debug_filename}' - Tìm thấy đối tượng tại {loc}.")
    else:
        print(f"Consolog: Debug image '{debug_filename}' - Không tìm thấy đối tượng.")
    return loc

def click_image_in_hwnd(hwnd, image_path, confidence=0.8):
    """
    Xác định tọa độ của hình ảnh trên screen và thực hiện click tại tọa độ đó
    trong không gian client của cửa sổ hwnd.
    Trả về True nếu thành công, False nếu không.
    """
    client_point = get_image_coordinates_in_hwnd(hwnd, image_path, confidence)
    if client_point is not None:
        click_at(hwnd, client_point[0], client_point[1])
        print(f"Consolog: Click thành công hình {image_path} tại tọa độ client: {client_point} trong hwnd {hwnd}")
        return True
    else:
        print(f"Consolog: Không click được hình {image_path} vì không lấy được tọa độ trên hwnd {hwnd}.")
        return False

def dump_hwnd_image(hwnd, filename):
    """
    Dump lại khung của cửa sổ hwnd ra file ảnh bằng PrintWindow để debug cấu trúc giao diện.
    """
    try:
        left, top, right, bot = win32gui.GetWindowRect(hwnd)
        width = right - left
        height = bot - top
        hwndDC = win32gui.GetWindowDC(hwnd)
        mfcDC = win32ui.CreateDCFromHandle(hwndDC)
        saveDC = mfcDC.CreateCompatibleDC()
        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
        saveDC.SelectObject(saveBitMap)
        result = win32gui.PrintWindow(hwnd, saveDC.GetSafeHdc(), 0)
        if result == 1:
            saveBitMap.SaveBitmapFile(saveDC, filename)
            print(f"Consolog: Dump hình hwnd thành công, lưu tại {filename}")
        else:
            print("Consolog: Lỗi khi dump hình hwnd.")
        win32gui.ReleaseDC(hwnd, hwndDC)
        win32gui.DeleteObject(saveBitMap.GetHandle())
    except Exception as e:
        print("Consolog: Lỗi khi sử dụng PrintWindow:", e)

def capture_debug_screenshot(hwnd, debug_filename):
    """
    Capture debug screenshot của vùng client của cửa sổ hwnd và lưu vào file debug_filename.
    """
    if not win32gui.IsWindow(hwnd):
        print("Consolog: HWND không hợp lệ trong debug capture.")
        return
    client_origin = win32gui.ClientToScreen(hwnd, (0, 0))
    client_rect = win32gui.GetClientRect(hwnd)
    width = client_rect[2]
    height = client_rect[3]
    region = (client_origin[0], client_origin[1], width, height)
    try:
        screenshot = pyautogui.screenshot(region=region)
        screenshot.save(debug_filename)
        print(f"Consolog: Debug capture đã lưu ảnh tại {debug_filename}.")
    except Exception as e:
        print(f"Consolog: Lỗi khi chụp debug screenshot: {e}")

def automate_contact_process(welcome_message_default, phone_number, hwnd):
    """
    Quy trình tự động hoá trên 1 cửa sổ (hwnd). Các thao tác locate – chuyển đổi – click được thực hiện
    trong không gian của cửa sổ đó bằng các hàm hỗ trợ.
    """
    print("Consolog: Delay 3s trước Bước 1")
    sleep_with_pause(3)

    # --- BƯỚC 1‑3: Capture ảnh giao diện tĩnh (Static UI) --- 
    static_ui_image = os.path.join(IMAGE_DIR, "cropped_20250411_121250.png")
    print("Consolog: Bước 1‑3: Capture static UI debug image.")
    check_image_debug(hwnd, static_ui_image, debug_filename="debug_step1_static_ui.png", confidence=0.8)

    # --- BƯỚC 1: Click menu --- 
    menu_image = os.path.join(IMAGE_DIR, "cropped_20250411_121250.png")
    if click_image_in_hwnd(hwnd, menu_image, confidence=0.8):
        print("Consolog: Bước 1: Click menu thành công.")
    else:
        print("Consolog: Bước 1: Không tìm thấy hình menu.")
    sleep_with_pause(2)

    # --- BƯỚC 2: Click \"add contact\" --- 
    add_contact_image = os.path.join(IMAGE_DIR, "cropped_20250404_063240.png")
    if click_image_in_hwnd(hwnd, add_contact_image, confidence=0.8):
        print("Consolog: Bước 2: Click add contact thành công.")
    else:
        print("Consolog: Bước 2: Không tìm thấy hình add contact.")
    sleep_with_pause(2)

    # --- BƯỚC 3: Click \"thêm contact\" --- 
    them_contact_image = os.path.join(IMAGE_DIR, "cropped_20250404_063308.png")
    if click_image_in_hwnd(hwnd, them_contact_image, confidence=0.8):
        print("Consolog: Bước 3: Click thêm contact thành công.")
    else:
        print("Consolog: Bước 3: Không tìm thấy hình thêm contact.")
    sleep_with_pause(2)

    # --- BƯỚC DEBUG cho nhóm bước 1‑3 --- 
    print("Consolog: Bước 1‑3: Capture debug screenshot sau khi hoàn tất bước 1‑3.")
    capture_debug_screenshot(hwnd, "debug_step3_after.png")

    # --- BƯỚC 4: Nhập tên theo định dạng SDT + ngày tháng --- 
    phone_path = get_settings().get("phone_path")
    random_phone = "0123456789"  # Giá trị mặc định
    if phone_path and os.path.exists(phone_path):
        try:
            with open(phone_path, "r", encoding="utf-8") as f:
                phone_list = [line.strip() for line in f if line.strip()]
            if phone_list:
                random_phone = random.choice(phone_list)
                phone_list.remove(random_phone)
                with open(phone_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(phone_list))
                print("Consolog: Đã xóa SDT khỏi file cấu hình và không để lại khoảng trắng.")
                with open(DATA_PROCESS_FILE, "a", encoding="utf-8") as f_dp:
                    f_dp.write(f"{random_phone}_{hwnd}\n")
                print(f"Consolog: Ghi số điện thoại {random_phone} và hwnd {hwnd} vào file {DATA_PROCESS_FILE}.")
            else:
                print("Consolog: File số điện thoại rỗng, dùng mặc định.")
        except Exception as e:
            print("Consolog: Lỗi khi đọc hoặc ghi file số điện thoại:", e)
    else:
        print("Consolog: Không tìm thấy file cấu hình số điện thoại, dùng mặc định.")

    date_str = time.strftime("%d%m%Y")
    name = f"{random_phone}_{date_str}"
    send_text_via_post(hwnd, name)
    print(f"Consolog: Bước 4: Nhập tên {name}.")
    sleep_with_pause(2)

    # --- BƯỚC DEBUG 4: Capture debug screenshot sau khi nhập tên --- 
    print("Consolog: Bước 4: Capture debug screenshot sau khi nhập tên contact.")
    capture_debug_screenshot(hwnd, "debug_step4_after.png")

    # --- BƯỚC 5: Chuyển focus sang trường số điện thoại (Tab) --- 
    print("Consolog: Bước 5: Chuyển focus sang trường số điện thoại bằng cách nhấn Tab 1 lần sử dụng pyautogui.press()")
    pyautogui.press("tab")
    sleep_with_pause(0.2)
    print("Consolog: Bước 5: Nhấn Tab 1 lần thành công.")
    sleep_with_pause(2)

    # --- BƯỚC 6: Xoá nội dung cũ và điền SDT lấy từ data_process.text --- 
    print("Consolog: Bước 6: Ctrl+A và Delete bằng pyautogui do đã focus đúng.")
    pyautogui.hotkey('ctrl', 'a')
    sleep_with_pause(0.2)
    pyautogui.press('delete')
    sleep_with_pause(0.5)

    sdt_to_fill = None
    phone_process_file = DATA_PROCESS_FILE
    if os.path.exists(phone_process_file):
        try:
            with open(phone_process_file, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]
            for line in lines:
                if "_" in line:
                    parts = line.split("_")
                    if parts[-1] == str(hwnd):
                        sdt_to_fill = parts[0]
                        print(f"Consolog: Tìm thấy số điện thoại {sdt_to_fill} cho hwnd {hwnd} trong {phone_process_file}.")
                        break
            if sdt_to_fill is None:
                print(f"Consolog: Không tìm thấy số điện thoại tương ứng cho hwnd {hwnd} trong {phone_process_file}. Sử dụng mặc định.")
                sdt_to_fill = "0123456789"
        except Exception as e:
            print(f"Consolog: Lỗi khi đọc file {phone_process_file}: {e}")
            sdt_to_fill = "0123456789"
    else:
        print(f"Consolog: File {phone_process_file} không tồn tại. Sử dụng số mặc định.")
        sdt_to_fill = "0123456789"

    pyautogui.write(sdt_to_fill)
    print(f"Consolog: Bước 6: Xóa nội dung cũ và nhập số điện thoại: {sdt_to_fill} bằng pyautogui.")
    sleep_with_pause(2)

    # --- BƯỚC DEBUG 6: Capture debug screenshot sau khi nhập số điện thoại --- 
    print("Consolog: Bước 6: Capture debug screenshot sau khi nhập số điện thoại.")
    capture_debug_screenshot(hwnd, "debug_step6_after.png")

    # --- BƯỚC 6.1: Tìm và click ảnh cropped_20250410_232349.png --- 
    image_path_step6_extra = os.path.join(IMAGE_DIR, "cropped_20250410_232349.png")
    print("Consolog: Bước 6.1: Tìm ảnh cropped_20250410_232349.png sau khi nhập số điện thoại và tiến hành click.")
    if click_image_in_hwnd(hwnd, image_path_step6_extra, confidence=0.8):
        print("Consolog: Bước 6.1: Click ảnh cropped_20250410_232349.png thành công.")
    else:
        print("Consolog: Bước 6.1: Không tìm thấy ảnh cropped_20250410_232349.png.")
    sleep_with_pause(2)

    # --- BƯỚC 8: Kiểm tra ảnh điều kiện & xử lý --- 
    image_path_step5 = os.path.join(IMAGE_DIR, "cropped_20250412_223952.png")
    print("Consolog: Bước 8: Kiểm tra ảnh điều kiện với delay và debug image 'debug_step8_after.png'.")
    exists = image_exists_in_hwnd(hwnd, image_path_step5, confidence=0.8, debug_filename="debug_step8_after.png", extra_delay=1.5)
    if not exists:
        print("Consolog: Bước 8: Không tìm thấy ảnh, chuyển sang bước 9.")
        sleep_with_pause(2)
    else:
        print("Consolog: Bước 8: Tìm thấy ảnh, tiến hành xóa sdt_hwnd khỏi file data_process.text và khôi phục sdt gốc vào file phone_path.txt.")
        phone_process_file = DATA_PROCESS_FILE
        updated_lines = []
        removed_phone = None
        if os.path.exists(phone_process_file):
            try:
                with open(phone_process_file, "r", encoding="utf-8") as f:
                    lines = [line.strip() for line in f if line.strip()]
                for line in lines:
                    if "_" in line:
                        parts = line.split("_")
                        if parts[-1] == str(hwnd):
                            removed_phone = parts[0]
                            print(f"Consolog: Xóa sdt {removed_phone} cho hwnd {hwnd} khỏi {phone_process_file}.")
                            continue
                    updated_lines.append(line)
                with open(phone_process_file, "w", encoding="utf-8") as f:
                    f.write("\n".join(updated_lines))
            except Exception as e:
                print(f"Consolog: Lỗi khi xử lý file {phone_process_file}: {e}")
        else:
            print(f"Consolog: File {phone_process_file} không tồn tại. Không có gì để xóa.")

        if removed_phone:
            phone_path_file = get_settings().get("phone_path")
            if phone_path_file:
                try:
                    with open(phone_path_file, "a", encoding="utf-8") as f:
                        f.write(f"\n{removed_phone}")
                    print(f"Consolog: Đã khôi phục sdt {removed_phone} vào file {phone_path_file}.")
                except Exception as e:
                    print(f"Consolog: Lỗi khi khôi phục sdt vào file {phone_path_file}: {e}")
            else:
                print("Consolog: File cấu hình phone_path không được xác định.")
        else:
            print("Consolog: Không tìm thấy sdt nào tương ứng với hwnd trong file data_process.text.")
        return

    # --- BƯỚC 7: Kiểm tra cảnh báo trùng SDT --- 
    warning_image = os.path.join(IMAGE_DIR, "duplicate_phone_warning.png")
    print("Consolog: Bước 7: Kiểm tra cảnh báo trùng SDT với debug image 'debug_step7_after.png'.")
    loc_warning = check_image_debug(hwnd, warning_image, debug_filename="debug_step7_after.png",
                                    confidence=0.8, extra_delay=1.0)
    if loc_warning:
        print("Consolog: Bước 7: Phát hiện cảnh báo trùng SDT.")
    else:
        print("Consolog: Bước 7: Không phát hiện cảnh báo trùng SDT.")

    # --- BƯỚC 9: Nhập tin nhắn chào mừng và gửi --- 
    send_text_via_post(hwnd, welcome_message_default)
    print(f"Consolog: Bước 9: Nhập tin nhắn: {welcome_message_default}")
    sleep_with_pause(1)
    print("Consolog: Bước 9: Gửi tin nhắn xong.")
    sleep_with_pause(1)
    
    print("Consolog: Bước 9: Đợi 2s sau khi ấn Enter để bắt đầu kiểm tra hình ảnh xác nhận.")
    sleep_with_pause(2)
    
    image_path_step7 = os.path.join(IMAGE_DIR, "cropped_20250411_042803.png")
    print("Consolog: Bước 9: Kiểm tra ảnh xác nhận, debug image 'debug_step9_after.png'.")
    loc7 = check_image_debug(hwnd, image_path_step7, debug_filename="debug_step9_after.png", confidence=0.8)
    if loc7 is not None:
        print("Consolog: Bước 9: Tìm thấy hình xác nhận, thực hiện khôi phục SĐT.")
        phone_process_file = DATA_PROCESS_FILE
        updated_lines = []
        removed_phone = None
        if os.path.exists(phone_process_file):
            try:
                with open(phone_process_file, "r", encoding="utf-8") as f:
                    lines = [line.strip() for line in f if line.strip()]
                for line in lines:
                    if "_" in line:
                        parts = line.split("_")
                        if parts[-1] == str(hwnd):
                            removed_phone = parts[0]
                            print(f"Consolog: Xóa sdt {removed_phone} cho hwnd {hwnd} khỏi {phone_process_file}.")
                            continue
                    updated_lines.append(line)
                with open(phone_process_file, "w", encoding="utf-8") as f:
                    f.write("\n".join(updated_lines))
            except Exception as e:
                print(f"Consolog: Lỗi khi xử lý file {phone_process_file}: {e}")
        if removed_phone:
            phone_path_file = get_settings().get("phone_path")
            if phone_path_file:
                try:
                    with open(phone_path_file, "a", encoding="utf-8") as f:
                        f.write(f"\n{removed_phone}")
                    print(f"Consolog: Đã khôi phục sdt {removed_phone} vào file {phone_path_file}.")
                except Exception as e:
                    print(f"Consolog: Lỗi khi khôi phục sdt vào file {phone_path_file}: {e}")
            else:
                print("Consolog: File cấu hình phone_path không được xác định.")
        else:
            print("Consolog: Không tìm thấy sdt nào tương ứng với hwnd trong file data_process.text.")
        if 'auto_thread' in globals():
            if auto_thread.is_alive():
                print("Consolog: Đang chờ auto_thread kết thúc...")
                auto_thread.join()
                print("Consolog: auto_thread đã kết thúc.")
        else:
            print("Consolog: Không tìm thấy auto_thread để chờ kết thúc.")

def click_first_conversation_via_post(hwnd):
    x, y = 50, 150
    click_at(hwnd, x, y)

def main():
    if len(sys.argv) < 3:
        print("Usage: script_welcome.py <tdata_folder> <hwnd> [welcome_message]")
        sys.exit(1)
    tdata_folder = sys.argv[1]
    try:
        global hwnd
        hwnd = int(sys.argv[2])
    except ValueError:
        print("Consolog: HWND không hợp lệ")
        sys.exit(1)
    settings = get_settings()
    welcome_message = settings.get("welcome_message") or "Chào mừng bạn đến với Telegram!"
    if len(sys.argv) >= 4:
        welcome_message = sys.argv[3]
    print("Consolog: Trước khi gọi SetForegroundWindow, hwnd =", hwnd)
    try:
        win32gui.SetForegroundWindow(hwnd)
        print("Consolog: Sau khi gọi SetForegroundWindow, hwnd =", hwnd)
    except Exception as e:
        print("Consolog: Lỗi khi gọi SetForegroundWindow:", e)
    try:
        is_visible = win32gui.IsWindowVisible(hwnd)
        rect = win32gui.GetWindowRect(hwnd)
        print(f"Consolog: Cửa sổ hwnd = {hwnd}, IsWindowVisible = {is_visible}, Rect = {rect}")
    except Exception as e:
        print("Consolog: Lỗi khi lấy thông tin cửa sổ:", e)
    dump_hwnd_image(hwnd, "debug_hwnd_dump.bmp")
    automate_contact_process(welcome_message, phone_number=settings.get("phone_path") or "0123456789", hwnd=hwnd)
    click_first_conversation_via_post(hwnd)
    sleep_with_pause(2)
    
if __name__ == "__main__":
    main()
