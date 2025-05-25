import tkinter as tk

class StatsPanel(tk.Frame):
    """
    Khu vực hiển thị thống kê (stats, logged, summary)
    """
    def __init__(self, master, lang):
        super().__init__(master)
        self.label = tk.Label(self, text=lang["stats_label"])
        self.label.pack()
        self.text = tk.Text(self, width=70, height=10)
        self.text.pack()

    def set_stats(self, value):
        self.text.delete("1.0", tk.END)
        self.text.insert(tk.END, value)
