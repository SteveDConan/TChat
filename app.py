import os
import time
import threading
import tkinter as tk

from ui.main_ui import init_main_ui
from core.language import select_language
from core.update_utils import check_for_updates
from core.language import lang  # Import từ điển lang

def load_tool(splash):
    """Perform initial loading of the tool"""
    start_time = time.time()
    print("Consolog: Starting tool load...")
    # Add any necessary initialization here
    time.sleep(2)  # Simulated loading time
    end_time = time.time()
    print("Consolog: Tool loaded in {:.2f} seconds.".format(end_time - start_time))
    splash.after(0, lambda: finish_splash(splash))

def finish_splash(splash):
    """Close splash screen and show language selection"""
    splash.destroy()
    print("Consolog: Splash screen closed, showing language selection.")
    select_language()

def show_splash_screen():
    """Display initial loading splash screen"""
    splash = tk.Tk()
    splash.overrideredirect(True)
    width = 300
    height = 150
    screen_width = splash.winfo_screenwidth()
    screen_height = splash.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    splash.geometry(f"{width}x{height}+{x}+{y}")
    
    # Dùng phương thức .get() để tránh KeyError nếu không có 'title' trong từ điển lang
    title = lang.get("title", "Default Title")  # Nếu không có, sẽ trả về "Default Title"
    
    label = tk.Label(splash, text=title, font=("Arial Unicode MS", 12))
    label.pack(expand=True)
    print("Consolog: Splash screen displayed.")

    threading.Thread(target=lambda: load_tool(splash), daemon=True).start()
    splash.mainloop()

if __name__ == "__main__":
    print("Consolog: Application starting, displaying splash screen...")
    show_splash_screen()
