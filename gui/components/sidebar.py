import customtkinter as ctk
from gui.theme import (
    ThemeManager, H2, H3, BODY, SMALL,
    PAD_SM, PAD_MD, PAD_LG,
    SIDEBAR_W, SIDEBAR_COLLAPSED, RADIUS,
)


class SidebarItem(ctk.CTkFrame):

    def __init__(self, parent, icon: str, label: str,
                 command=None, is_active: bool = False, collapsed: bool = False):
        tm = ThemeManager()
        bg = tm.c("ACCENT_DIM") if is_active else "transparent"
        super().__init__(parent, fg_color=bg, corner_radius=8, height=42)
        self.pack_propagate(False)

        self._tm = tm
        self._icon = icon
        self._label_text = label
        self._command = command
        self._is_active = is_active
        self._collapsed = collapsed

        self._indicator = ctk.CTkFrame(
            self, width=3, height=28,
            fg_color=tm.c("ACCENT") if is_active else "transparent",
            corner_radius=2,
        )
        self._indicator.pack(side="left", padx=(4, 0), pady=7)

        self._icon_label = ctk.CTkLabel(
            self, text=icon, font=("Helvetica", 18),
            text_color=tm.c("ACCENT") if is_active else tm.c("TEXT_SECONDARY"),
            width=36,
        )
        self._icon_label.pack(side="left", padx=(4, 0))

        self._text_label = ctk.CTkLabel(
            self, text=label, font=BODY,
            text_color=tm.c("TEXT_PRIMARY") if is_active else tm.c("TEXT_SECONDARY"),
            anchor="w",
        )
        if not collapsed:
            self._text_label.pack(side="left", padx=(4, 0), fill="x", expand=True)

        self.bind("<Button-1>", self._on_click)
        self._icon_label.bind("<Button-1>", self._on_click)
        self._text_label.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

        self._tooltip = None

    def _on_click(self, event=None):
        if self._command:
            self._command()

    def _on_enter(self, event=None):
        if not self._is_active:
            self.configure(fg_color=self._tm.c("BG_HOVER"))
        if self._collapsed:
            self._show_tooltip()

    def _on_leave(self, event=None):
        if not self._is_active:
            self.configure(fg_color="transparent")
        self._hide_tooltip()

    def _show_tooltip(self):
        if self._tooltip:
            return
        x = self.winfo_rootx() + self.winfo_width() + 5
        y = self.winfo_rooty() + 5
        self._tooltip = tk_tooltip = ctk.CTkToplevel(self)
        tk_tooltip.wm_overrideredirect(True)
        tk_tooltip.geometry(f"+{x}+{y}")
        tk_tooltip.configure(fg_color=self._tm.c("BG_ELEVATED"))
        label = ctk.CTkLabel(
            tk_tooltip, text=self._label_text, font=SMALL,
            text_color=self._tm.c("TEXT_PRIMARY"),
            fg_color=self._tm.c("BG_ELEVATED"),
            padx=8, pady=4,
        )
        label.pack()

    def _hide_tooltip(self):
        if self._tooltip:
            try:
                self._tooltip.destroy()
            except Exception:
                pass
            self._tooltip = None

    def set_active(self, active: bool):
        self._is_active = active
        if active:
            self.configure(fg_color=self._tm.c("ACCENT_DIM"))
            self._indicator.configure(fg_color=self._tm.c("ACCENT"))
            self._icon_label.configure(text_color=self._tm.c("ACCENT"))
            self._text_label.configure(text_color=self._tm.c("TEXT_PRIMARY"))
        else:
            self.configure(fg_color="transparent")
            self._indicator.configure(fg_color="transparent")
            self._icon_label.configure(text_color=self._tm.c("TEXT_SECONDARY"))
            self._text_label.configure(text_color=self._tm.c("TEXT_SECONDARY"))

    def set_collapsed(self, collapsed: bool):
        self._collapsed = collapsed
        if collapsed:
            self._text_label.pack_forget()
        else:
            self._text_label.pack(side="left", padx=(4, 0), fill="x", expand=True)


class AnimatedSidebar(ctk.CTkFrame):

    NAV_ITEMS = [
        ("⊞", "Dashboard", "dashboard"),
        ("👥", "Teams", "teams"),
        ("⚔", "Matches", "matches"),
        ("🏆", "Bracket", "bracket"),
        ("📊", "Rankings", "rankings"),
        ("⚙", "Settings", "settings"),
    ]

    def __init__(self, parent, on_navigate=None):
        tm = ThemeManager()
        super().__init__(
            parent, fg_color=tm.c("BG_SURFACE"),
            width=SIDEBAR_W, corner_radius=0,
            border_width=0,
        )
        self.pack_propagate(False)

        self._tm = tm
        self._on_navigate = on_navigate
        self._collapsed = False
        self._current_width = SIDEBAR_W
        self._target_width = SIDEBAR_W
        self._active_view = "dashboard"
        self._items: dict = {}

        self._logo_frame = ctk.CTkFrame(self, fg_color="transparent", height=60)
        self._logo_frame.pack(fill="x", padx=PAD_SM, pady=(PAD_MD, PAD_SM))
        self._logo_frame.pack_propagate(False)

        self._logo_icon = ctk.CTkLabel(
            self._logo_frame, text="⚡", font=("Helvetica", 24),
            text_color=tm.c("ACCENT"),
        )
        self._logo_icon.pack(side="left", padx=(PAD_SM, PAD_SM))

        self._logo_text = ctk.CTkLabel(
            self._logo_frame, text="EsportsHub",
            font=H2, text_color=tm.c("TEXT_PRIMARY"),
        )
        self._logo_text.pack(side="left")

        sep = ctk.CTkFrame(self, height=1, fg_color=tm.c("BORDER"))
        sep.pack(fill="x", padx=PAD_MD, pady=PAD_SM)

        self._nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._nav_frame.pack(fill="x", padx=PAD_SM, pady=PAD_SM)

        for icon, label, view_name in self.NAV_ITEMS:
            is_active = view_name == self._active_view
            item = SidebarItem(
                self._nav_frame, icon=icon, label=label,
                command=lambda v=view_name: self._navigate(v),
                is_active=is_active,
            )
            item.pack(fill="x", pady=2)
            self._items[view_name] = item

        spacer = ctk.CTkFrame(self, fg_color="transparent")
        spacer.pack(fill="both", expand=True)

        self._toggle_frame = ctk.CTkFrame(self, fg_color="transparent", height=50)
        self._toggle_frame.pack(fill="x", side="bottom", padx=PAD_SM, pady=PAD_MD)
        self._toggle_frame.pack_propagate(False)

        self._toggle_btn = ctk.CTkButton(
            self._toggle_frame, text="←", width=36, height=36,
            fg_color="transparent", hover_color=tm.c("BG_HOVER"),
            text_color=tm.c("TEXT_SECONDARY"), font=H3,
            corner_radius=8, command=self.toggle,
        )
        self._toggle_btn.pack(side="right" if not self._collapsed else "center")

    def _navigate(self, view_name: str):
        self._active_view = view_name
        for name, item in self._items.items():
            item.set_active(name == view_name)
        if self._on_navigate:
            self._on_navigate(view_name)

    def toggle(self):
        self._collapsed = not self._collapsed
        self._target_width = SIDEBAR_COLLAPSED if self._collapsed else SIDEBAR_W
        self._toggle_btn.configure(text="→" if self._collapsed else "←")
        self._animate_step(0)

    def _animate_step(self, step):
        total_steps = 8
        if step >= total_steps:
            self._current_width = self._target_width
            self.configure(width=self._target_width)
            self._update_collapsed_state()
            return

        progress = (step + 1) / total_steps
        progress = 1 - (1 - progress) ** 2
        new_width = self._current_width + (self._target_width - self._current_width) * progress
        self.configure(width=int(new_width))
        self.after(12, lambda: self._animate_step(step + 1))

    def _update_collapsed_state(self):
        if self._collapsed:
            self._logo_text.pack_forget()
        else:
            self._logo_text.pack(side="left")

        for item in self._items.values():
            item.set_collapsed(self._collapsed)

    def set_active(self, view_name: str):
        self._active_view = view_name
        for name, item in self._items.items():
            item.set_active(name == view_name)
