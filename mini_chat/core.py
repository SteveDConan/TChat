import os

# Consolog: Thiết lập TESSDATA_PREFIX để Tesseract có thể tải các file ngôn ngữ đúng cách
# Sửa: Chỉ định thư mục tessdata chứa các file traineddata
os.environ["TESSDATA_PREFIX"] = r"C:\Program Files\Tesseract-OCR\tessdata\\"

import openai
import pytesseract


pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
import hashlib
from langdetect import detect
import threading
import time
import tkinter as tk
from tkinter import messagebox
import ctypes
import math
import shutil
import re  # Consolog: Thêm import re để trích xuất thông tin ngôn ngữ từ phản hồi ChatGPT

# Import components
from .vocab_widget import VocabWidget

# Consolog: Thêm import psutil để nhận diện tiến trình Telegram
try:
    import psutil
except ImportError:
    psutil = None

# Consolog: Các biến và hàm toàn cục dành riêng cho Mini Chat
root = None  # Biến root sẽ được set từ app.py
CHATGPT_API_KEY = None
TRANSLATION_ONLY = True
DEFAULT_TARGET_LANG = "en"

# Consolog: Thêm biến cho ngôn ngữ của tôi và của đối phương (mặc định)
# [CHANGED]: Đổi MY_LANG_SELECTION từ 'en' thành 'vi' để phù hợp với yêu cầu hiển thị nội dung dịch sang ngôn ngữ của bạn.
MY_LANG_SELECTION = "vi"
TARGET_LANG_SELECTION = DEFAULT_TARGET_LANG

# Consolog: Thêm biến cấu hình DPI, mặc định bật (True)
DPI_ENABLED = True

# Consolog: Thêm biến để tạm dừng/khôi phục mini chat nhằm tiết kiệm chi phí ChatGPT API
mini_chat_paused = False
mini_chat_pause_button = None  # Sẽ được khởi tạo trong create_mini_chat()

# Consolog: THÊM BIẾN THEO DÕI THỜI GIAN HOẠT ĐỘNG TRONG MINI CHAT
# [ADDED - INACTIVITY]: Lưu thời điểm tương tác cuối cùng của mini chat (chỉ áp dụng cho mini chat, không dùng cho widget mini chatgpt)
mini_chat_last_active_time = time.time()

# Consolog: Các biến và hàm toàn cục dành riêng cho widget mini chatgpt (mới bổ sung)
mini_chatgpt_win = None
mini_chatgpt_entry = None
# Consolog [REMOVED]: Biến riêng cho widget mini chat pause. Chúng ta sẽ dùng chung trạng thái tạm dừng với mini chat.
# mini_chatgpt_paused = False
mini_chatgpt_pause_button = None  # Biến toàn cục cho nút Pause của widget mini chatgpt
# (Sau này nút này sẽ được đổi thành nút Zoom theo yêu cầu)

# ========================
# [ADDED]: Thêm biến toàn cục lưu HWND Telegram lần cuối được ưu tiên
last_valid_telegram_hwnd = None
# ========================

# [ADDED]: Biến cờ để kiểm soát thread của widget mini chatgpt, dùng để dừng thread khi destroy
widget_mini_chat_thread_running = True
print(
    "Consolog: Đã khởi tạo biến widget_mini_chat_thread_running = True để quản lý thread widget mini chat."
)

# ----- module-level, đặt ngay dưới import tkinter as tk, threading, … -----
LANG_CODE_TO_NAME = {
    "en": "English",      
    "zh": "Chinese", 
    "vi": "Vietnamese",    
    "ar": "Arabic-Egypt",      # Egypt
    "bn": "Bangladesh",        # Bangladesh
    "pt": "Brazil",            # Brazil
    "am": "Ethiopia",          # Ethiopia
    "fr": "French",
    "de": "German",
    "id": "Indonesian",
    "km": "Khmer",
    "es": "Spanish-Mexico",    # Mexico
    "tl": "Philippines",       # Philippines
    "yo": "Nigeria",           # Nigeria (local)
}
# LANG_CODE_TO_NAME = {
#     "en": "English",
#     "vi": "Vietnamese",
#     "fr": "French",
#     "es": "Spanish",
#     "de": "German",
#     "zh": "Chinese",
#     "km": "Khmer",
#     "pt": "Portuguese",
# }
NAME_TO_LANG_CODE = {name: code for code, name in LANG_CODE_TO_NAME.items()}

# Shared StringVar cho cả hai widget
target_lang_display_var = tk.StringVar(
    value=LANG_CODE_TO_NAME.get(TARGET_LANG_SELECTION, "English")
)


# Consolog: Tạo hàm nhận root từ app.py (để Mini Chat có thể dùng)
def set_root(r):
    global root
    root = r


# Consolog: Tạo hàm nhận các biến cài đặt liên quan ChatGPT từ app.py
def set_mini_chat_globals(api_key, translation_only_flag, default_lang):
    global CHATGPT_API_KEY, TRANSLATION_ONLY, DEFAULT_TARGET_LANG
    CHATGPT_API_KEY = api_key
    TRANSLATION_ONLY = translation_only_flag
    DEFAULT_TARGET_LANG = default_lang
    print("Consolog: Đã set các biến toàn cục cho mini_chat.py")


# Hàm load cấu hình từ file config.ini
def load_config():
    global MY_LANG_SELECTION, TARGET_LANG_SELECTION, DPI_ENABLED
    config_file = os.path.join(os.getcwd(), "config.ini")
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or "=" not in line:
                        continue
                    key, value = line.split("=", 1)
                    if key == "MY_LANG_SELECTION":
                        MY_LANG_SELECTION = value
                    elif key == "TARGET_LANG_SELECTION":
                        TARGET_LANG_SELECTION = value
                    elif key == "DPI_ENABLED":
                        DPI_ENABLED = True if value.lower() == "true" else False
            print("Consolog: Đã load cấu hình từ file config.ini")
        except Exception as e:
            print(f"Consolog [ERROR]: Lỗi load config: {e}")
    else:
        print("Consolog: Không tìm thấy file config.ini, sử dụng cấu hình mặc định")


# Gọi hàm load_config khi module được khởi tạo
load_config()

# Biến cho Mini Chat
mini_chat_win = None
mini_chat_text = None
mini_chat_entry = None

# Dictionary lưu lại ảnh chụp trước đó theo hwnd (dùng để so sánh SSIM)
screenshot_images = {}

# Lưu log dịch (theo hwnd)
translation_logs = {}

# Lưu ngôn ngữ đối phương theo hwnd
hwnd_target_lang = {}

user32 = ctypes.windll.user32

###############################################################
# Consolog: CÁC HÀM LIÊN QUAN ĐẾN MINI CHAT ĐƯỢC TÁCH TỪ app.py
###############################################################


# Consolog: Hàm mapping ngôn ngữ từ menu sang tham số ngôn ngữ của Tesseract
def get_ocr_lang(lang):
    ocr_lang_map = {
        "en": "eng",
        "vi": "vie",
        "fr": "fra",
        "es": "spa",
        "de": "deu",
        "zh": "chi_sim+chi_tra",
        "km": "khm",
        "pt": "por",
    }
    mapped_lang = ocr_lang_map.get(lang.lower(), "eng")
    print(f"Consolog: Mapping OCR cho ngôn ngữ '{lang}' thành '{mapped_lang}'")
    return mapped_lang


def toggle_mini_chat_pause():
    global mini_chat_paused, mini_chat_pause_button, mini_chatgpt_pause_button
    mini_chat_paused = not mini_chat_paused
    if mini_chat_paused:
        if mini_chat_pause_button:
            mini_chat_pause_button.config(text="Resume")
        if mini_chatgpt_pause_button:
            mini_chatgpt_pause_button.config(text="Resume")
        print("Consolog: Mini Chat đã được tạm dừng.")
        append_mini_chat("Mini Chat đã được tạm dừng.")
    else:
        if mini_chat_pause_button:
            mini_chat_pause_button.config(text="Pause")
        if mini_chatgpt_pause_button:
            mini_chatgpt_pause_button.config(text="Pause")
        print("Consolog: Mini Chat đã được phục hồi.")
        append_mini_chat("Mini Chat đã được phục hồi.")


# Mini chat ô to
def create_mini_chat():
    global mini_chat_win, mini_chat_text, mini_chat_entry
    global TARGET_LANG_SELECTION, MY_LANG_SELECTION, DPI_ENABLED, mini_chat_pause_button

    if root is None:
        print(
            "Consolog [ERROR]: root chưa được set trong mini chat. Gọi set_root(root) trước khi tạo mini chat."
        )
        return

    mini_chat_win = tk.Toplevel(root)
    mini_chat_win.title("Mini Chat")

    # Vị trí cửa sổ
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    width, height = 530, 350
    x = screen_width - width - 10
    y = screen_height - height - 10
    mini_chat_win.geometry(f"{width}x{height}+{x}+{y}")
    mini_chat_win.attributes("-topmost", True)

    # --- MENU CHỌN NGÔN NGỮ & DPI ---
    menu_frame = tk.Frame(mini_chat_win)
    menu_frame.pack(side=tk.TOP, fill=tk.X, pady=5)

    # My Language
    tk.Label(menu_frame, text="My Language:").pack(side=tk.LEFT, padx=5)
    my_lang_display_var = tk.StringVar(
        value=LANG_CODE_TO_NAME.get(MY_LANG_SELECTION, "Vietnamese")
    )
    my_lang_display_options = list(LANG_CODE_TO_NAME.values())

    def on_my_lang_display_select(chosen_name):
        global MY_LANG_SELECTION
        MY_LANG_SELECTION = NAME_TO_LANG_CODE[chosen_name]
        print(f"Consolog: Đã cập nhật ngôn ngữ của tôi: {MY_LANG_SELECTION}")

    my_lang_menu = tk.OptionMenu(
        menu_frame,
        my_lang_display_var,
        *my_lang_display_options,
        command=on_my_lang_display_select,
    )
    my_lang_menu.pack(side=tk.LEFT, padx=5)

    # Target Language
    tk.Label(menu_frame, text="Target Language:").pack(side=tk.LEFT, padx=5)
    target_lang_display_options = list(LANG_CODE_TO_NAME.values())

    def on_target_lang_display_select(chosen_name):
        global TARGET_LANG_SELECTION
        TARGET_LANG_SELECTION = NAME_TO_LANG_CODE[chosen_name]
        print(f"Consolog: Đã cập nhật ngôn ngữ của đối phương: {TARGET_LANG_SELECTION}")

    target_lang_menu = tk.OptionMenu(
        menu_frame,
        target_lang_display_var,
        *target_lang_display_options,
        command=on_target_lang_display_select,
    )
    target_lang_menu.pack(side=tk.LEFT, padx=5)

    # DPI checkbox
    dpi_var = tk.BooleanVar(value=DPI_ENABLED)

    def update_dpi():
        global DPI_ENABLED
        DPI_ENABLED = dpi_var.get()
        print(f"Consolog: Cập nhật DPI_ENABLED thành: {DPI_ENABLED}")

    dpi_checkbox = tk.Checkbutton(
        menu_frame, text="DPI", variable=dpi_var, command=update_dpi
    )
    dpi_checkbox.pack(side=tk.LEFT, padx=5)

    # Save button
    save_button = tk.Button(menu_frame, text="Save", command=save_config)
    save_button.pack(side=tk.LEFT, padx=5)

    # Khung hiển thị tin nhắn
    mini_chat_text = tk.Text(mini_chat_win, height=15, width=60, state=tk.DISABLED)
    mini_chat_text.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    # Khung nhập tin nhắn và các nút
    frame_input = tk.Frame(mini_chat_win)
    frame_input.pack(side=tk.BOTTOM, fill=tk.X)

    mini_chat_entry = tk.Entry(frame_input, width=50)
    mini_chat_entry.pack(side=tk.LEFT, padx=5, pady=5)
    mini_chat_entry.bind("<Return>", lambda event: send_mini_chat_message())

    btn_send = tk.Button(frame_input, text="Send", command=send_mini_chat_message)
    btn_send.pack(side=tk.LEFT, padx=5)

    mini_chat_pause_button = tk.Button(
        frame_input, text="Pause", command=toggle_mini_chat_pause
    )
    mini_chat_pause_button.pack(side=tk.LEFT, padx=5)

    btn_clear = tk.Button(frame_input, text="Clear", command=clear_mini_chat)
    btn_clear.pack(side=tk.LEFT, padx=5)

    # Khởi động thread theo dõi inactivity
    threading.Thread(target=mini_chat_inactivity_monitor, daemon=True).start()

    print("Consolog: Đã khởi tạo Mini Chat với dropdown hiển thị tên ngôn ngữ đầy đủ.")


def clear_mini_chat():
    global mini_chat_text
    if mini_chat_text is not None:
        mini_chat_text.config(state=tk.NORMAL)
        mini_chat_text.delete("1.0", tk.END)
        mini_chat_text.config(state=tk.DISABLED)
        print("Consolog: Đã xóa toàn bộ text trong mini chat.")


def append_mini_chat(text):
    global mini_chat_text
    if mini_chat_text is None:
        return
    mini_chat_text.config(state=tk.NORMAL)
    mini_chat_text.insert(tk.END, text + "\n")
    mini_chat_text.see(tk.END)
    mini_chat_text.config(state=tk.DISABLED)


# -----------------------------------------------
# Phần bổ sung: Hàm tiền xử lý ảnh và OCR với log chi tiết
from PIL import Image, ImageEnhance, ImageFilter


def preprocess_image(image):
    print("Consolog: Bắt đầu tiền xử lý ảnh cho OCR.")
    print(f"Consolog: Ảnh đầu vào - kích thước: {image.size}, chế độ: {image.mode}")

    # ✅ 1. Resize ảnh lên x2 trước khi xử lý (resize càng sớm càng tốt)
    image = image.resize((image.width * 4, image.height * 4), Image.LANCZOS)
    print(f"Consolog: Đã phóng to ảnh lên kích thước: {image.size}")

    # Chuyển ảnh về dạng grayscale
    image = image.convert("L")
    print("Consolog: Đã chuyển ảnh sang grayscale.")

    # ✅ 2. Tăng độ nét: sử dụng bộ lọc SHARPEN (nếu cần mạnh hơn có thể dùng UnsharpMask)
    image = image.filter(ImageFilter.SHARPEN)
    print("Consolog: Đã áp dụng bộ lọc SHARPEN để tăng độ nét.")

    # ✅ 3. Tăng contrast nhẹ: sử dụng hệ số 1.8 để làm chữ nổi bật
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.8)
    print("Consolog: Đã tăng độ tương phản của ảnh.")

    # ✅ 4. Không dùng threshold (nhị phân) nếu ảnh đã rõ nét
    print(
        f"Consolog: Ảnh sau tiền xử lý - kích thước: {image.size}, chế độ: {image.mode}"
    )
    return image


def perform_ocr(image, lang="eng+chi_sim+chi_tra"):
    print("Consolog: Bắt đầu thực hiện OCR với ngôn ngữ: " + lang)
    print(f"Consolog: Kích thước ảnh đầu vào: {image.size}, chế độ ảnh: {image.mode}")

    # Tiền xử lý ảnh để cải thiện kết quả OCR
    processed_image = preprocess_image(image)

    # Bổ sung log: Lưu ảnh sau tiền xử lý để debug
    processed_image.save("debug_ocr.png")
    print("Consolog: Đã lưu ảnh sau tiền xử lý thành debug_ocr.png")

    custom_config = (
        "--psm 6"  # Cấu hình tùy chỉnh cho OCR (có thể điều chỉnh theo bố cục văn bản)
    )
    print("Consolog: Đang thực hiện OCR với cấu hình: " + custom_config)

    ocr_text = pytesseract.image_to_string(
        processed_image, lang=lang, config=custom_config
    )
    print("Consolog: Kết quả OCR thô: " + ocr_text)
    return ocr_text


# -----------------------------------------------


def translate_text_via_chatgpt(
    text, source_lang="auto", target_lang="en", conversation_context=""
):
    global CHATGPT_API_KEY
    if not CHATGPT_API_KEY:
        append_mini_chat("Mini Chat [ERROR]: ChatGPT API key not set.")
        return text, None

    try:
        openai.api_key = CHATGPT_API_KEY

        # Consolog: Tạo mapping từ mã ngôn ngữ sang tên tiếng Việt cho prompt
        lang_map = {
            "vi": "tiếng Việt",
            "en": "tiếng Anh",
            "zh": "tiếng Trung",  # tiếng Trung Quốc
            "km": "tiếng Khmer",  # tiếng Campuchia (Khmer)
            "pt": "tiếng Bồ Đào Nha",  # Brazil dùng tiếng Bồ Đào Nha
            "bn": "tiếng Bengal",  # Bangladesh
            "tl": "tiếng Tagalog",  # Philippines
            "am": "tiếng Amhara",  # Ethiopia
            "ar": "tiếng Ả Rập",  # Egypt
            "es": "tiếng Tây Ban Nha",  # Mexico
            "id": "tiếng Indonesia",  # Indonesia
            "yo": "tiếng Yoruba-Nigeria",       # Nigeria (local)
        }
        # Dùng mapping nếu có, ngược lại giữ nguyên giá trị target_lang
        lang_name = lang_map.get(target_lang.lower(), target_lang)

        prompt = (
            f"Hãy chuyển ngữ đoạn văn dưới đây sang {lang_name} một cách chính xác, tự nhiên và sát nghĩa nhất, giống như khi ChatGPT dịch trực tiếp trên nền tảng web. "
            f"Trước khi dịch, **đọc kỹ câu chat và hiểu ngữ cảnh**: Xem câu chat đó đang nói về điều gì, hoàn cảnh như thế nào, và tìm cách dịch sao cho sát nghĩa nhất, "
            f"**không sáng tạo thành một câu khác nghĩa**. Nếu không hiểu được ngữ cảnh, hãy **dùng cách dịch từng từ một** (word by word) để đảm bảo không bị thay đổi ý nghĩa.\n"
            f"Lưu ý quan trọng: Câu gốc là một câu **thân mật**, sử dụng 'em' và 'anh' trong ngữ cảnh gần gũi, không phải là 'bạn' và 'anh ta'. "
            f"Trong tiếng Việt, 'em' và 'anh' thể hiện sự gần gũi và thân mật, vậy nên khi dịch, bạn cần duy trì sự thân mật này trong ngữ cảnh giao tiếp. "
            f"Không dịch theo nghĩa đen, mà phải giữ đúng ngữ nghĩa và phong cách giao tiếp tự nhiên. "
            f"**Nếu câu thiếu từ hoặc dấu câu**, không thêm từ vào, chỉ dịch chính xác và giữ nguyên ý định câu.\n"
            f"3. Đảm bảo kết quả cuối cùng chỉ bao gồm văn bản đã chuyển ngữ, không kèm theo ghi chú hay chỉ dẫn nào khác.\n"
            f"4. Đọc kỹ câu văn, bao gồm cả những câu lóng, kiểu nói địa phương hay cách nói chuyện thường gặp. Dịch sao cho dễ hiểu, mượt mà và giữ nguyên bản chất câu nói.\n\n"
            f"Nội dung cần dịch:\n{text}\n\n"
            f"Bối cảnh: {conversation_context}.\n\n"
            f"Chỉ in kết quả cuối cùng là văn bản đã chuyển ngữ."
        )

        print(
            "Consolog: Đã cập nhật prompt dịch theo yêu cầu mới (bao gồm chỉ dẫn xử lý câu lóng và địa phương):"
        )
        print(prompt)

        # Consolog: [CHANGED] Sử dụng mô hình ChatGPT 4o thay vì gpt-3.5-turbo
        print("Consolog: Đang sử dụng mô hình ChatGPT 4o để thực hiện dịch.")
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
        )

        # Truy xuất nội dung từ phản hồi ChatGPT
        full_reply = response["choices"][0]["message"]["content"].strip()
        print(f"Consolog: Kết quả dịch thô từ ChatGPT: {full_reply}")

        detected_lang = None

        # Loại bỏ các dòng chỉ dẫn không cần thiết nếu có
        new_full_reply = re.sub(
            r"^(Chuyển\s+ngữ\s+sang\s+.+?:\s*)", "", full_reply, flags=re.IGNORECASE
        )
        if new_full_reply != full_reply:
            print("Consolog: Đã loại bỏ dòng thừa từ phản hồi ChatGPT.")
            full_reply = new_full_reply

        # Sử dụng regex để tìm header [Ngôn ngữ: ...] hoặc [Language: ...]
        matches = list(
            re.finditer(
                r"\[(?:Ngôn\s*ngữ|Language):\s*(.*?)\]", full_reply, re.IGNORECASE
            )
        )
        if matches:
            detected_lang = matches[-1].group(1).strip()
            # Loại bỏ header, chỉ lấy nội dung sau header cuối cùng
            translated_text = full_reply[matches[-1].end() :].strip()
            print(
                f"Consolog: Phát hiện header ngôn ngữ, loại bỏ: {matches[-1].group(0)}"
            )
        else:
            translated_text = full_reply.strip()
            print("Consolog: Không phát hiện header ngôn ngữ trong phản hồi ChatGPT.")

        print("Consolog: Kết quả dịch đã được làm sạch:")
        print(translated_text)
        return translated_text, detected_lang

    except openai.error.OpenAIError as e:
        append_mini_chat(f"Mini Chat [ERROR]: OpenAI API error: {e}")
        return text, None
    except Exception as e:
        append_mini_chat(f"Mini Chat [ERROR]: Translation error: {e}")
        return text, None


def send_message_to_telegram_input(hwnd, message):
    # Consolog [CHANGED]: Tin nhắn gửi vào Telegram là message đã được dịch, không có thêm bất kỳ nội dung phụ nào.
    rect = ctypes.wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    width = rect.right - rect.left
    x = rect.left + width // 2
    y = rect.bottom - 3  # cách viền dưới 3px

    # Di chuyển chuột đến vị trí và click
    ctypes.windll.user32.SetCursorPos(x, y)
    time.sleep(0.1)
    ctypes.windll.user32.mouse_event(2, 0, 0, 0, 0)  # Chuột trái xuống
    time.sleep(0.05)
    ctypes.windll.user32.mouse_event(4, 0, 0, 0, 0)  # Chuột trái nhả
    time.sleep(0.1)

    # Copy tin nhắn vào clipboard
    root.clipboard_clear()
    root.clipboard_append(message)
    root.update()
    time.sleep(0.1)

    # Giả lập Ctrl+V để dán
    VK_CONTROL = 0x11
    VK_V = 0x56
    VK_RETURN = 0x0D

    ctypes.windll.user32.keybd_event(VK_CONTROL, 0, 0, 0)
    time.sleep(0.05)
    ctypes.windll.user32.keybd_event(VK_V, 0, 0, 0)
    time.sleep(0.05)
    ctypes.windll.user32.keybd_event(VK_V, 0, 2, 0)
    time.sleep(0.05)
    ctypes.windll.user32.keybd_event(VK_CONTROL, 0, 2, 0)
    time.sleep(0.1)

    # Giả lập Enter để gửi
    ctypes.windll.user32.keybd_event(VK_RETURN, 0, 0, 0)
    time.sleep(0.05)
    ctypes.windll.user32.keybd_event(VK_RETURN, 0, 2, 0)
    time.sleep(0.1)


# =============================================================================
# [CHANGED]: BỎ HÀM get_active_telegram_hwnd() cũ và thay thế bằng hàm get_correct_telegram_hwnd()
# =============================================================================
def get_correct_telegram_hwnd():
    """
    Consolog: Hàm này dùng để lấy hwnd của cửa sổ Telegram ưu tiên.
    Yêu cầu mới: Nếu cửa sổ foreground thuộc Telegram và không bị thu nhỏ, trả về hwnd đó.
    Nếu cửa sổ foreground không phải Telegram hoặc đang thu nhỏ, thì giữ lại HWND của lần Telegram trước đó nếu không thu nhỏ.
    Nếu không có HWND Telegram nào được lưu (hoặc cửa sổ trước đó thu nhỏ), dùng EnumWindows để quét và tìm cửa sổ Telegram không bị thu nhỏ.
    """
    global last_valid_telegram_hwnd
    hwnd_fore = user32.GetForegroundWindow()
    pid = ctypes.wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd_fore, ctypes.byref(pid))
    try:
        proc = psutil.Process(pid.value)
        if proc.name().lower() == "telegram.exe":
            if not user32.IsIconic(
                hwnd_fore
            ):  # Consolog [ADDED]: Kiểm tra cửa sổ không bị thu nhỏ
                last_valid_telegram_hwnd = hwnd_fore
                print(
                    f"Consolog [INFO]: Active Telegram HWND từ foreground (không bị thu nhỏ): {hwnd_fore}"
                )
                return hwnd_fore
            else:
                print("Consolog: Cửa sổ foreground Telegram đang thu nhỏ.")
    except Exception as e:
        print(f"Consolog [ERROR]: Lỗi kiểm tra cửa sổ foreground Telegram: {e}")

    if last_valid_telegram_hwnd is not None and not user32.IsIconic(
        last_valid_telegram_hwnd
    ):
        print(
            f"Consolog [INFO]: Sử dụng last_valid_telegram_hwnd: {last_valid_telegram_hwnd}"
        )
        return last_valid_telegram_hwnd

    # Nếu không có HWND hợp lệ, dùng EnumWindows để quét
    hwnd_result = None
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)

    def enum_windows_proc(hwnd, lParam):
        nonlocal hwnd_result
        if user32.IsWindowVisible(hwnd) and not user32.IsIconic(
            hwnd
        ):  # Consolog [ADDED]: Bỏ qua các cửa sổ thu nhỏ
            length = user32.GetWindowTextLengthW(hwnd)
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            title = buff.value
            pid_local = ctypes.wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid_local))
            try:
                proc = psutil.Process(pid_local.value)
                if proc.name().lower() == "telegram.exe":
                    hwnd_result = hwnd
                    last_valid_telegram_hwnd = hwnd  # Cập nhật last_valid_telegram_hwnd
                    print(
                        f"Consolog [INFO]: Tìm thấy cửa sổ Telegram (không thu nhỏ) với tiêu đề: {title}, PID={pid_local.value}"
                    )
                    return False  # Dừng quét sau khi tìm được cửa sổ phù hợp
            except Exception as e:
                print(f"Consolog [ERROR]: Lỗi lấy thông tin tiến trình: {e}")
        return True

    enum_proc_c = EnumWindowsProc(enum_windows_proc)
    user32.EnumWindows(enum_proc_c, 0)
    print(f"Consolog [INFO]: Correct Telegram HWND được lấy (sau enum): {hwnd_result}")
    return hwnd_result


# =============================================================================
# Các chỗ gọi get_active_telegram_hwnd() đã được thay thế bằng get_correct_telegram_hwnd()
# =============================================================================


def detect_language_by_hwnd(hwnd):
    # Chụp ảnh cửa sổ => OCR => detect => trả về
    try:
        image = capture_window(hwnd)
        # Consolog [CHANGED-OCR]: Xác định ngôn ngữ áp dụng cho OCR dựa theo menu của đối phương
        lang_for_ocr = hwnd_target_lang.get(hwnd, TARGET_LANG_SELECTION)
        ocr_lang = get_ocr_lang(lang_for_ocr)
        text = perform_ocr(image, lang=ocr_lang)
        if text.strip():
            detected_lang = detect(text)
            print(
                f"Consolog: Đã phát hiện ngôn ngữ của đối phương HWND={hwnd}: {detected_lang}"
            )
            return detected_lang
        else:
            print(
                f"Consolog: Không phát hiện nội dung từ HWND={hwnd}, dùng mặc định {DEFAULT_TARGET_LANG}"
            )
            return DEFAULT_TARGET_LANG
    except Exception as e:
        print(f"Consolog [ERROR]: Lỗi detect lang HWND={hwnd}: {e}")
        return DEFAULT_TARGET_LANG


def capture_window(hwnd):
    # Consolog: Kiểm tra cấu hình DPI trước khi gọi SetProcessDPIAware
    if DPI_ENABLED:
        ctypes.windll.user32.SetProcessDPIAware()
        print(
            "Consolog: DPI_ENABLED=True, đã gọi SetProcessDPIAware để đảm bảo đo theo DPI chính xác."
        )
    else:
        print("Consolog: DPI_ENABLED=False, bỏ qua gọi SetProcessDPIAware.")

    # Consolog: Dùng ShowWindow để đảm bảo cửa sổ không bị thu nhỏ, kích thước ảnh sẽ đúng kích thước HWND.
    user32.ShowWindow(hwnd, 9)  # SW_RESTORE
    time.sleep(0.2)
    print(
        "Consolog: Đã gọi ShowWindow(SW_RESTORE) để đảm bảo cửa sổ hiển thị đầy đủ trước khi chụp."
    )

    gdi32 = ctypes.windll.gdi32
    rect = ctypes.wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    width = rect.right - rect.left
    height = rect.bottom - rect.top
    print(f"Consolog: Kích thước cửa sổ: width={width}, height={height}")

    hwindc = user32.GetWindowDC(hwnd)
    srcdc = gdi32.CreateCompatibleDC(hwindc)
    bmp = gdi32.CreateCompatibleBitmap(hwindc, width, height)
    gdi32.SelectObject(srcdc, bmp)

    print("Consolog: Đang gọi PrintWindow với flag 0 để capture toàn bộ cửa sổ.")
    result = user32.PrintWindow(hwnd, srcdc, 0)
    if result != 1:
        print(
            "Consolog [WARNING]: PrintWindow không thành công hoặc chỉ chụp được 1 phần."
        )

    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [
            ("biSize", ctypes.c_uint32),
            ("biWidth", ctypes.c_int32),
            ("biHeight", ctypes.c_int32),
            ("biPlanes", ctypes.c_uint16),
            ("biBitCount", ctypes.c_uint16),
            ("biCompression", ctypes.c_uint32),
            ("biSizeImage", ctypes.c_uint32),
            ("biXPelsPerMeter", ctypes.c_int32),
            ("biYPelsPerMeter", ctypes.c_int32),
            ("biClrUsed", ctypes.c_uint32),
            ("biClrImportant", ctypes.c_uint32),
        ]

    bmi = BITMAPINFOHEADER()
    bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.biWidth = width
    bmi.biHeight = -height
    bmi.biPlanes = 1
    bmi.biBitCount = 32
    bmi.biCompression = 0

    buffer_len = width * height * 4
    buffer = ctypes.create_string_buffer(buffer_len)
    _ = gdi32.GetDIBits(srcdc, bmp, 0, height, buffer, ctypes.byref(bmi), 0)

    from PIL import Image

    image = Image.frombuffer("RGBA", (width, height), buffer, "raw", "BGRA", 0, 1)
    img_width, img_height = image.size
    if img_width != width or img_height != height:
        print(
            f"Consolog: Cảnh báo! Kích thước ảnh chụp ({img_width}x{img_height}) không khớp với kích thước HWND ({width}x{height})."
        )
        print(
            "Consolog: Thực hiện fallback capture với ImageGrab dựa vào tọa độ cửa sổ."
        )
        # Giải phóng các đối tượng đã sử dụng
        gdi32.DeleteObject(bmp)
        gdi32.DeleteDC(srcdc)
        user32.ReleaseDC(hwnd, hwindc)
        from PIL import ImageGrab

        image = ImageGrab.grab(bbox=(rect.left, rect.top, rect.right, rect.bottom))
        img_width, img_height = image.size
        if img_width != width or img_height != height:
            print(
                f"Consolog [ERROR]: Fallback capture cũng không thành công, kích thước ảnh chụp: {img_width}x{img_height}"
            )
        else:
            print(
                "Consolog: Fallback capture thành công, kích thước ảnh chụp khớp với kích thước HWND."
            )
    else:
        print("Consolog: Kích thước ảnh chụp khớp với kích thước HWND.")
        gdi32.DeleteObject(bmp)
        gdi32.DeleteDC(srcdc)
        user32.ReleaseDC(hwnd, hwindc)

    return image


def send_mini_chat_message():
    global mini_chat_entry, mini_chat_text, hwnd_target_lang, TARGET_LANG_SELECTION, mini_chat_paused, mini_chat_last_active_time
    if mini_chat_entry is None:
        return
    # [ADDED - INACTIVITY]: Cập nhật thời gian hoạt động của mini chat khi có thao tác (send message)
    mini_chat_last_active_time = time.time()
    # Nếu mini chat đang ở trạng thái tạm dừng do inactivity, tự động khôi phục
    if mini_chat_paused:
        mini_chat_paused = False
        if mini_chat_pause_button:
            mini_chat_pause_button.config(text="Pause")
        append_mini_chat("Mini Chat auto resumed do có thao tác từ người dùng.")
        print("Consolog: Mini Chat auto resumed do có thao tác từ người dùng.")

    msg = mini_chat_entry.get().strip()
    if not msg:
        return
    mini_chat_entry.delete(0, tk.END)

    # Consolog: Ghi log tin nhắn gốc của người dùng vào Mini Chat (không gửi qua Telegram)
    append_mini_chat("You: " + msg)

    # [CHANGED]: Sử dụng get_correct_telegram_hwnd() thay cho get_active_telegram_hwnd()
    hwnd = get_correct_telegram_hwnd()
    if hwnd is None:
        append_mini_chat(
            "Mini Chat [ERROR]: Không tìm thấy cửa sổ Telegram đang active."
        )
        return

    # Consolog: Kiểm tra và đảm bảo đã xác định ngôn ngữ cho HWND trước khi dịch tin nhắn
    target_lang = hwnd_target_lang.get(hwnd)
    if not target_lang:
        print(
            "Consolog: Chưa có ngôn ngữ xác định cho HWND, sử dụng ngôn ngữ được chọn từ menu."
        )
        target_lang = TARGET_LANG_SELECTION
        hwnd_target_lang[hwnd] = TARGET_LANG_SELECTION

    # Consolog: Sử dụng ngôn ngữ của đối phương từ menu cho tin nhắn chat gửi vào Telegram:
    print(
        f"Consolog: Sử dụng ngôn ngữ của đối phương từ menu: {TARGET_LANG_SELECTION} cho tin nhắn chat gửi vào Telegram."
    )

    # Consolog: Đã xác định ngôn ngữ cho HWND, tiến hành dịch tin nhắn theo ngôn ngữ đó.
    translated, detected = translate_text_via_chatgpt(
        msg, source_lang="auto", target_lang=target_lang
    )
    # Consolog [CHANGED]: Luôn giữ nguyên ngôn ngữ được chọn từ config, không cập nhật theo kết quả detected từ ChatGPT.

    # Consolog: Ghi log tin nhắn đã dịch vào Mini Chat (chỉ nội dung dịch)
    append_mini_chat(translated)

    # Consolog [CHANGED]: Tin nhắn gửi vào Telegram là duy nhất nội dung đã được dịch (không thêm thông tin phụ)
    print("Consolog: Đang gửi tin nhắn đã dịch vào Telegram.")
    try:
        send_message_to_telegram_input(hwnd, translated)
        # Consolog [CHANGED]:
        # Sau khi gửi, thêm delay ngắn, đưa cửa sổ mini chat lên foreground và ép focus vào ô nhập.
        time.sleep(0.1)
        if mini_chat_win:
            mini_chat_win.lift()
        if mini_chat_entry:
            mini_chat_entry.focus_force()
        print(
            "Consolog: Focus đã được đặt lại vào ô mini chat sau khi gửi tin thành công."
        )
    except Exception as e:
        append_mini_chat(f"Mini Chat [ERROR]: Lỗi gửi tin nhắn: {e}")


def mini_chat_monitor():
    """
    Luồng chạy nền: mỗi 3 giây sẽ quét cửa sổ Telegram foreground, chụp screenshot,
    so sánh bằng SSIM, nếu có thay đổi đáng kể => OCR => gọi ChatGPT => hiển thị kết quả trong mini chat.
    Chỉ dịch 1 lần khi phát hiện ảnh mới của từng hwnd.
    """
    TEMP_FOLDER = os.path.join(os.getcwd(), "mini_chat_screenshots")
    os.makedirs(TEMP_FOLDER, exist_ok=True)

    while True:
        # Consolog: Kiểm tra trạng thái tạm dừng của mini chat để tiết kiệm chi phí ChatGPT API (chỉ ảnh hưởng đến dịch incoming)
        if mini_chat_paused:
            print(
                "Consolog: Mini Chat đang tạm dừng, bỏ qua việc quét cửa sổ Telegram."
            )
            time.sleep(3)
            continue

        time.sleep(3)
        hwnd_fore = user32.GetForegroundWindow()
        pid = ctypes.wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd_fore, ctypes.byref(pid))

        try:
            process = psutil.Process(pid.value)
            if process.name().lower() != "telegram.exe":
                continue
        except:
            continue

        try:
            img = capture_window(hwnd_fore)
        except Exception as e:
            append_mini_chat(f"Mini Chat [ERROR]: Capture window failed: {e}")
            continue

        # So sánh ảnh hiện tại với ảnh đã lưu trước đó bằng SSIM
        prev_image = screenshot_images.get(hwnd_fore)
        if prev_image is not None:
            from skimage.metrics import structural_similarity as ssim
            import numpy as np

            # Chuyển đổi ảnh sang grayscale và chuyển về mảng numpy
            img1 = np.array(prev_image.convert("L"))
            img2 = np.array(img.convert("L"))
            # Kiểm tra kích thước của hai ảnh
            if img1.shape != img2.shape:
                print(
                    f"Consolog: Kích thước ảnh cũ {img1.shape} không khớp với ảnh mới {img2.shape}, coi là thay đổi."
                )
                score = 0
            else:
                score, _ = ssim(img1, img2, full=True)
                print(f"Consolog: SSIM score cho HWND {hwnd_fore}: {score}")
            if score >= 0.99:  # Ngưỡng có thể điều chỉnh
                print(
                    f"Consolog: Không có thay đổi đáng kể (SSIM >= 0.99) cho HWND {hwnd_fore}, bỏ qua dịch."
                )
                continue

        # Cập nhật ảnh mới vào dictionary
        screenshot_images[hwnd_fore] = img
        print(
            f"Consolog: Ảnh mới cho HWND {hwnd_fore} phát hiện, tiến hành OCR và dịch."
        )
        filename = os.path.join(TEMP_FOLDER, f"{hwnd_fore}_screenshot.png")
        img.save(filename)

        try:
            # Consolog [CHANGED-OCR]: Xác định ngôn ngữ áp dụng cho OCR dựa theo menu của đối phương
            lang_for_ocr = hwnd_target_lang.get(hwnd_fore, TARGET_LANG_SELECTION)
            ocr_lang = get_ocr_lang(lang_for_ocr)
            ocr_text = perform_ocr(img, lang=ocr_lang)
        except Exception as e:
            append_mini_chat(f"Mini Chat [ERROR]: OCR failed: {e}")
            continue

        if not ocr_text.strip():
            continue

        prev_ocr = translation_logs.get(hwnd_fore, {}).get("ocr")
        if prev_ocr and prev_ocr.strip() == ocr_text.strip():
            print(
                f"Consolog: Nội dung OCR cho HWND {hwnd_fore} không thay đổi, bỏ qua dịch."
            )
            continue

        # Consolog: Dùng ngôn ngữ của tôi (MY_LANG_SELECTION) làm target cho dịch tin nhắn đến tôi từ OCR
        print(
            f"Consolog: Sử dụng ngôn ngữ của tôi từ menu: {MY_LANG_SELECTION} cho bản dịch tin nhắn đến từ OCR."
        )
        translation, detected = translate_text_via_chatgpt(
            ocr_text,
            source_lang="auto",
            target_lang=MY_LANG_SELECTION,
            conversation_context="Conversation transcript translation",
        )

        translation_logs[hwnd_fore] = {"ocr": ocr_text, "translation": translation}
        print(
            "Consolog: Đang đẩy nội dung dịch đã được làm sạch vào mini chat (không thêm chú thích)."
        )
        append_mini_chat(translation)


def start_mini_chat_monitor():
    t = threading.Thread(target=mini_chat_monitor, daemon=True)
    t.start()


# Consolog: [ADDED - INACTIVITY]: Hàm giám sát thời gian inactivity của mini chat
def mini_chat_inactivity_monitor():
    global mini_chat_last_active_time, mini_chat_paused
    while True:
        # Chỉ áp dụng cho mini chat; widget mini chatgpt không ảnh hưởng tới biến này
        if (
            not mini_chat_paused and (time.time() - mini_chat_last_active_time) >= 180
        ):  # 180 giây = 3 phút
            mini_chat_paused = True
            if mini_chat_pause_button:
                mini_chat_pause_button.config(text="Resume")
            append_mini_chat(
                "Mini Chat paused do 3 phút inactivity để tiết kiệm API tokens."
            )
            print(
                "Consolog: Mini Chat paused tự động do không có hoạt động trong 3 phút."
            )
        time.sleep(1)


# Consolog: Hàm lưu cài đặt ngôn ngữ và DPI vào file config (ví dụ: config.ini)
def save_config():
    try:
        config_file = os.path.join(os.getcwd(), "config.ini")
        with open(config_file, "w", encoding="utf-8") as f:
            f.write(f"MY_LANG_SELECTION={MY_LANG_SELECTION}\n")
            f.write(f"TARGET_LANG_SELECTION={TARGET_LANG_SELECTION}\n")
            f.write(f"DPI_ENABLED={DPI_ENABLED}\n")
        print("Consolog: Đã lưu cài đặt ngôn ngữ và DPI vào file config.ini")

        # Consolog: Cập nhật ngay lập tức cấu hình ngôn ngữ cho các cửa sổ chat hiện tại
        for hwnd in list(hwnd_target_lang.keys()):
            hwnd_target_lang[hwnd] = TARGET_LANG_SELECTION
            print(
                f"Consolog: Cập nhật ngôn ngữ đối phương cho HWND {hwnd} thành {TARGET_LANG_SELECTION} ngay sau khi lưu."
            )

        append_mini_chat("Cài đặt ngôn ngữ và DPI đã được lưu.")
    except Exception as e:
        print(f"Consolog [ERROR]: Lỗi lưu cài đặt config: {e}")
        append_mini_chat("Mini Chat [ERROR]: Lỗi lưu cài đặt config.")


# Consolog: Bổ sung hàm destroy_mini_chat() để đóng cửa sổ mini chat
def destroy_mini_chat():
    global mini_chat_win
    if mini_chat_win is not None:
        mini_chat_win.destroy()
        mini_chat_win = None
        print("Consolog: Mini chat window has been destroyed.")


###############################################
# PHẦN BỔ SUNG: Widget MINI CHATGPT (TÁCH RIÊNG)
###############################################

# Import ctypes.wintypes để định nghĩa cấu trúc WINDOWPLACEMENT
import ctypes.wintypes


# Định nghĩa cấu trúc WINDOWPLACEMENT để lấy thông tin vị trí cửa sổ "bình thường"
class WINDOWPLACEMENT(ctypes.Structure):
    _fields_ = [
        ("length", ctypes.c_uint),
        ("flags", ctypes.c_uint),
        ("showCmd", ctypes.c_uint),
        ("ptMinPosition", ctypes.wintypes.POINT),
        ("ptMaxPosition", ctypes.wintypes.POINT),
        ("rcNormalPosition", ctypes.wintypes.RECT),
    ]


# Mini chat input dài trên cửa sổ telegram
"""Tạo widget mini chatgpt với kích thước bằng ô input của mini chat, bao gồm nút Send, Zoom và Quit.
    Widget này luôn ở "đít" (bottom) của cửa sổ Telegram, tự động cập nhật vị trí khi cửa sổ di chuyển.
    """


def create_mini_chatgpt():
    """
    Tạo cửa sổ mini ChatGPT và tích hợp widget học từ vựng (VocabWidget) bên trái ô nhập.
    Các thành phần được sắp xếp theo thứ tự: VocabWidget | Input | Dropdown | Send | Quit.
    """

    global mini_chatgpt_win, mini_chatgpt_entry, mini_chatgpt_pause_button
    global target_lang_display_var  # <-- biến toàn cục hiển thị ngôn ngữ đích

    if root is None:
        print(
            "Consolog [ERROR]: root chưa được set. Gọi set_root(root) trước khi tạo widget mini chatgpt."
        )
        return

    # --- 1. Tạo cửa sổ toplevel ---
    mini_chatgpt_win = tk.Toplevel(root)
    mini_chatgpt_win.title("Mini ChatGPT Widget")
    mini_chatgpt_win.overrideredirect(True)
    mini_chatgpt_win.attributes("-topmost", False)

    widget_width, widget_height = 400, 40
    # Đặt widget sát mép trên của cửa sổ Telegram, cách trái 1px
    root.update_idletasks()
    tele_x = 1
    tele_y = root.winfo_rooty()
    mini_chatgpt_win.geometry(f"{widget_width}x{widget_height}+{tele_x}+{tele_y}")
    mini_chatgpt_win.withdraw()
    print(
        "Consolog: Widget mini chatgpt được khởi tạo và ẩn do chưa phát hiện được HWND của Telegram."
    )

    # --- 2. Frame chứa toàn bộ các widget chức năng ---
    frame = tk.Frame(mini_chatgpt_win)
    frame.pack(fill=tk.BOTH, expand=True)

    # --- 3. Thêm widget học từ vựng ở đầu hàng ---
    vocab_widget = VocabWidget(
        frame,
        vocab_file="mini_chat/vocabs/vocab_all.json",  # Đường dẫn file vocab
        width=290,
        height=52,  # Có thể chỉnh cao bằng chiều cao input cho đẹp hơn
    )
    vocab_widget.grid(row=0, column=0, padx=2, pady=2, sticky="nsew")

    # --- 4. Entry nhập nội dung ChatGPT (kế tiếp vocab_widget) ---
    mini_chatgpt_entry = tk.Entry(frame)
    mini_chatgpt_entry.grid(
        row=0,
        column=1,
        sticky="we",
        padx=4,
        pady=4,
        ipady=3,  # tăng chiều cao cho đẹp
    )
    mini_chatgpt_entry.config(bd=1, relief="solid", font=("Segoe UI", 10))
    mini_chatgpt_entry.bind("<Return>", lambda e: send_mini_chatgpt_message())

    # --- Đảm bảo input mở rộng khi kéo ngang ---
    frame.columnconfigure(1, weight=1)

    # --- 5. Dropdown chọn ngôn ngữ đích ---
    def on_target_lang_select(chosen_name):
        global TARGET_LANG_SELECTION
        TARGET_LANG_SELECTION = NAME_TO_LANG_CODE[chosen_name]
        print(f"Consolog: Đã cập nhật ngôn ngữ đích: {TARGET_LANG_SELECTION}")

    target_lang_menu = tk.OptionMenu(
        frame,
        target_lang_display_var,
        *LANG_CODE_TO_NAME.values(),
        command=on_target_lang_select,
    )
    target_lang_menu.grid(row=0, column=2, padx=4, pady=4)
    target_lang_menu.config(font=("Segoe UI", 9), bd=1, relief="solid")

    # --- 6. Nút Send ---
    btn_send = tk.Button(frame, text="Send", command=send_mini_chatgpt_message)
    btn_send.grid(row=0, column=3, padx=4, pady=4)
    btn_send.config(bd=1, relief="solid", font=("Segoe UI", 9), padx=4, pady=4)

    # --- 7. Nút Quit ---
    btn_quit = tk.Button(frame, text="x", command=destroy_mini_chatgpt)
    btn_quit.grid(row=0, column=4, padx=4, pady=4)
    btn_quit.config(bd=1, relief="solid", font=("Segoe UI", 9), padx=4, pady=4)

    # # Nếu muốn thêm nút Zoom, mở comment này
    # btn_zoom = tk.Button(frame, text="Zoom", command=toggle_mini_chat_zoom)
    # btn_zoom.grid(row=0, column=5, padx=4, pady=4)
    # btn_zoom.config(bd=1, relief="solid", font=("Segoe UI", 9), padx=4, pady=4)
    # mini_chatgpt_pause_button = btn_zoom

    print(
        "Consolog: Đã tạo widget mini chatgpt với học từ vựng, ô nhập, dropdown, nút Send, Quit."
    )

    # --- 8. Tự động cập nhật vị trí widget bám theo cửa sổ Telegram ---
    threading.Thread(target=update_mini_chatgpt_position, daemon=True).start()


def send_mini_chatgpt_message():
    """Xử lý gửi tin từ widget mini chatgpt.
    Hành động gửi tương tự như mini chat thông thường: lấy nội dung từ entry, dịch (nếu cần) và gửi vào cửa sổ Telegram.
    Khác duy nhất là sau khi gửi, focus sẽ được đặt lại vào ô chat của widget mini chatgpt.
    """
    global mini_chatgpt_entry

    if mini_chatgpt_entry is None:
        return

    # Consolog [MODIFIED - WIDGET]: Bỏ qua kiểm tra mini_chat_paused để widget luôn hoạt động độc lập.
    # if mini_chat_paused:
    #     print("Consolog: Widget mini chatgpt (chung với mini chat) đang tạm dừng, không gửi tin.")
    #     return

    msg = mini_chatgpt_entry.get().strip()
    if not msg:
        return
    mini_chatgpt_entry.delete(0, tk.END)
    print("Consolog: [mini chatgpt] Người dùng nhập: " + msg)

    hwnd = get_correct_telegram_hwnd()
    if hwnd is None:
        print(
            "Consolog [ERROR]: Widget mini chatgpt không tìm thấy cửa sổ Telegram đang active."
        )
        return

    # đảm bảo target_lang mặc định là 'en' nếu chưa có giá trị
    default_target = TARGET_LANG_SELECTION or "en"
    target_lang = hwnd_target_lang.get(hwnd, default_target)
    print(f"Consolog: [mini chatgpt] Sử dụng ngôn ngữ đối phương: {target_lang}")

    translated, _ = translate_text_via_chatgpt(
        msg, source_lang="auto", target_lang=target_lang
    )
    print("Consolog: [mini chatgpt] Tin nhắn sau dịch: " + translated)

    try:
        send_message_to_telegram_input(hwnd, translated)
        print("Consolog: [mini chatgpt] Tin nhắn đã được gửi vào Telegram.")
        mini_chatgpt_entry.focus_force()
        print(
            "Consolog: Focus đã được đặt lại vào ô chat của widget mini chatgpt sau khi gửi tin."
        )
    except Exception as e:
        print("Consolog [ERROR]: Widget mini chatgpt gặp lỗi khi gửi tin: " + str(e))


# ========================
# [MODIFIED]: Hàm destroy_mini_chatgpt được chỉnh sửa theo yêu cầu
# Khi destroy_mini_chatgpt() được gọi, ngoài đóng widget mini chatgpt thì sẽ:
#   - Gọi destroy_mini_chat() để tắt cửa sổ mini chat
#   - Đặt biến cờ widget_mini_chat_thread_running = False để dừng thread cập nhật vị trí widget mini chatgpt
# ========================
def destroy_mini_chatgpt():
    global mini_chatgpt_win, widget_mini_chat_thread_running
    print("Consolog: Đang tiến hành destroy_mini_chatgpt()...")
    # Gọi hàm destroy_mini_chat để đóng cửa sổ mini chat (nếu đang mở)
    destroy_mini_chat()
    # Đặt cờ để dừng thread của widget mini chatgpt
    widget_mini_chat_thread_running = False
    print(
        "Consolog: Đã đặt widget_mini_chat_thread_running = False để dừng các thread liên quan đến widget mini chat."
    )
    if mini_chatgpt_win is not None:
        mini_chatgpt_win.destroy()
        mini_chatgpt_win = None
        print("Consolog: Widget mini chatgpt đã bị đóng.")


def update_mini_chatgpt_position():

    global mini_chatgpt_win, widget_mini_chat_thread_running
    while mini_chatgpt_win is not None and widget_mini_chat_thread_running:
        mini_chatgpt_win.update_idletasks()
        hwnd = get_correct_telegram_hwnd()
        if hwnd and not user32.IsIconic(hwnd):
            # Khi tìm thấy cửa sổ Telegram và cửa sổ không bị thu nhỏ, hiển thị widget
            mini_chatgpt_win.deiconify()
            # Lấy thông tin vị trí của cửa sổ qua GetWindowPlacement
            placement = WINDOWPLACEMENT()
            placement.length = ctypes.sizeof(WINDOWPLACEMENT)
            user32.GetWindowPlacement(hwnd, ctypes.byref(placement))
            # Nếu cửa sổ không ở trạng thái bình thường (SW_SHOWNORMAL=1), dùng rcNormalPosition
            if placement.showCmd != 1:
                rect = placement.rcNormalPosition
                print(
                    "Consolog: Cửa sổ Telegram không ở trạng thái bình thường, sử dụng rcNormalPosition."
                )
            else:
                rect = ctypes.wintypes.RECT()
                user32.GetWindowRect(hwnd, ctypes.byref(rect))
            window_width = rect.right - rect.left

            # Consolog [MODIFIED]: Cập nhật widget có cùng chiều rộng với cửa sổ Telegram và nằm phía dưới đáy của Telegram.
            widget_width = window_width  # widget_width bằng chiều rộng của Telegram
            widget_height = 52  # Chiều cao widget cố định
            x = rect.left  # Đặt widget bắt đầu từ mép trái của cửa sổ Telegram
            # Tính tọa độ y: widget nằm phía dưới mép dưới của Telegram, cách mép dưới của Telegram 1px
            y = rect.bottom + 1
            new_geometry = f"{widget_width}x{widget_height}+{x}+{y}"
            mini_chatgpt_win.geometry(new_geometry)
            mini_chatgpt_win.lift()  # Đảm bảo widget luôn nằm trên cùng
            print(
                f"Consolog: Updated widget geometry to {new_geometry} attached to HWND {hwnd}. (Widget nằm phía dưới đáy của Telegram, margin 1px)"
            )
        else:
            # Nếu không tìm thấy cửa sổ Telegram hợp lệ hoặc cửa sổ đang thu nhỏ, ẩn widget
            mini_chatgpt_win.withdraw()
            print(
                "Consolog: Không phát hiện HWND Telegram hợp lệ hoặc cửa sổ đang thu nhỏ. Widget mini chatgpt được ẩn."
            )
        time.sleep(0.5)


# ========================
# [ADDED]: Hàm toggle_mini_chat_zoom cho nút Zoom trong widget mini chatgpt
# ========================
def toggle_mini_chat_zoom():
    """
    Khi nhấn nút Zoom trên widget mini chatgpt:
      - Nếu cửa sổ mini chat chưa được tạo hoặc đang bị ẩn/thu nhỏ, tự động tạo hoặc khôi phục lại mini chat.
      - Sau đó, cập nhật geometry của mini chat để có kích thước tiêu chuẩn 530x350 và cách cạnh phải, dưới màn hình 50px.
    """
    global mini_chat_win
    if mini_chat_win is None:
        print("Consolog: Mini chat chưa tồn tại, tạo mới mini chat.")
        create_mini_chat()
    else:
        state = mini_chat_win.state()
        if state in ("withdrawn", "iconic"):
            mini_chat_win.deiconify()
            print("Consolog: Mini chat đã được khôi phục từ trạng thái tắt/thu nhỏ.")
    # Cập nhật geometry với khoảng cách 50px so với cạnh phải và dưới màn hình
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    width = 530
    height = 350
    x = screen_width - width - 50  # Consolog: Sửa margin từ 10px thành 50px ở bên phải
    y = screen_height - height - 50  # Consolog: Sửa margin từ 10px thành 50px bên dưới
    mini_chat_win.geometry(f"{width}x{height}+{x}+{y}")
    print(
        "Consolog: Mini chat đã được thay đổi kích thước về kích thước tiêu chuẩn với margin 50px bên phải và dưới màn hình."
    )


# ========================
# KẾT THÚC: Các thay đổi đã bổ sung theo yêu cầu
# ========================
