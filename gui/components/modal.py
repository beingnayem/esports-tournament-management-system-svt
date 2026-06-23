import customtkinter as ctk
from gui.theme import ThemeManager, H2, BODY, PAD_MD, PAD_LG, RADIUS


class Modal(ctk.CTkToplevel):

    def __init__(self, parent, title: str = "Modal",
                 width: int = 500, height: int = 600,
                 on_close=None):
        super().__init__(parent)

        tm = ThemeManager()
        self._on_close = on_close

        self.title(title)
        self.geometry(f"{width}x{height}")
        self.resizable(False, False)
        self.configure(fg_color=tm.c("BG_ELEVATED"))

        self.transient(parent)
        self.update_idletasks()
        self.grab_set()
        self.update_idletasks()
        px = parent.winfo_x() + (parent.winfo_width() - width) // 2
        py = parent.winfo_y() + (parent.winfo_height() - height) // 2
        self.geometry(f"+{px}+{py}")

        self.bind("<Escape>", lambda e: self.close())
        self.protocol("WM_DELETE_WINDOW", self.close)

        header = ctk.CTkFrame(self, fg_color=tm.c("BG_SURFACE"), height=50,
                               corner_radius=0)
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)

        title_label = ctk.CTkLabel(
            header, text=title, font=H2,
            text_color=tm.c("TEXT_PRIMARY"),
        )
        title_label.pack(side="left", padx=PAD_LG, pady=PAD_MD)

        close_btn = ctk.CTkButton(
            header, text="✕", width=32, height=32,
            fg_color="transparent", hover_color=tm.c("BG_HOVER"),
            text_color=tm.c("TEXT_SECONDARY"), font=H2,
            command=self.close,
        )
        close_btn.pack(side="right", padx=PAD_MD, pady=PAD_MD)

        sep = ctk.CTkFrame(self, height=1, fg_color=tm.c("BORDER"))
        sep.pack(fill="x")

        self.body = ctk.CTkScrollableFrame(
            self, fg_color=tm.c("BG_ELEVATED"),
            corner_radius=0,
        )
        self.body.pack(fill="both", expand=True, padx=PAD_MD, pady=PAD_MD)

        self.footer = ctk.CTkFrame(self, fg_color=tm.c("BG_SURFACE"), height=60,
                                    corner_radius=0)
        self.footer.pack(fill="x", side="bottom")
        self.footer.pack_propagate(False)

        self._cancel_btn = ctk.CTkButton(
            self.footer, text="Cancel", width=100, height=36,
            fg_color="transparent", hover_color=tm.c("BG_HOVER"),
            text_color=tm.c("TEXT_SECONDARY"), border_width=1,
            border_color=tm.c("BORDER"), corner_radius=8,
            command=self.close,
        )
        self._cancel_btn.pack(side="right", padx=(0, PAD_MD), pady=12)

        self._action_btn = ctk.CTkButton(
            self.footer, text="Save", width=100, height=36,
            fg_color=tm.c("ACCENT"), hover_color=tm.c("ACCENT_HOVER"),
            text_color="#FFFFFF", corner_radius=8,
            command=self._on_action,
        )
        self._action_btn.pack(side="right", padx=(0, PAD_MD), pady=12)

    def set_action_text(self, text: str):
        self._action_btn.configure(text=text)

    def set_action_command(self, command):
        self._action_btn.configure(command=command)

    def _on_action(self):
        self.close()

    def close(self):
        if self._on_close:
            self._on_close()
        try:
            self.grab_release()
            self.destroy()
        except Exception:
            pass
