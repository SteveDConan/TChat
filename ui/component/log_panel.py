import tkinter as tk

class LogPanel(tk.Frame):
    """
    Khu vực hiển thị log ghi chú hoạt động
    """
    def __init__(self, master, lang):
        super().__init__(master)
        tk.Label(self, text=lang["log_label"]).pack()
        self.text = tk.Text(self, width=70, height=10)
        self.text.pack()

    def log(self, value):
        self.text.insert(tk.END, value + '\n')
        self.text.see(tk.END)
