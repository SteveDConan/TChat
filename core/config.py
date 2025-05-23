# Configuration variables for the Telegram Auto Tool

import os

# API Configuration
API_ID = 22379547
API_HASH = '9fc2845bde4b64a6a51320a8045c8178'

# Version Information
CURRENT_VERSION = "1.05"
VERSION_INFO = "Version 1.0.5 - Copyright SAMADS"
GITHUB_USER = "nunerit"
GITHUB_REPO = "TelegramAuto"

# File Paths
CONFIG_FILE = "config.txt"
WINDOW_SIZE_FILE = "window_size.txt"
MARKER_IMAGE_PATH = os.path.join(os.getcwd(), "assets", "marker_image.png")
MARKER_CONFIG_FILE = os.path.join(os.getcwd(), "assets", "marker_config.txt")
CHATGPT_API_KEY_FILE = "chatgpt_api_key.txt"

# Default Settings
DEFAULT_TELEGRAM_PATH = r"C:\Users\SAM\AppData\Roaming\Telegram Desktop\Telegram.exe"
DEFAULT_TARGET_LANG = "vi"
TRANSLATION_ONLY = True

# Window Arrangement Settings
arrange_width = 500
arrange_height = 504

def load_chatgpt_api_key():
    if os.path.exists(CHATGPT_API_KEY_FILE):
        with open(CHATGPT_API_KEY_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""

def save_chatgpt_api_key(key):
    with open(CHATGPT_API_KEY_FILE, "w", encoding="utf-8") as f:
        f.write(key)

# Initialize ChatGPT API Key
CHATGPT_API_KEY = load_chatgpt_api_key() 