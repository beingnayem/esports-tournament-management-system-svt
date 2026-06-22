import customtkinter as ctk
from gui.app import EsportsApp

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    app = EsportsApp()
    app.mainloop()
