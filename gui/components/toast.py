import customtkinter as ctk
from gui.theme import ThemeManager, BODY, SMALL, PAD_SM, PAD_MD, RADIUS


class ToastManager:

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._root = None
            cls._instance._toasts = []
            cls._instance._y_offset = 20
        return cls._instance

    def set_root(self, root):
        self._root = root

    def show(self, message: str, toast_type: str = "info", duration: int = 3000):
        if self._root is None:
            return
        toast = Toast(self._root, message=message, toast_type=toast_type,
                      duration=duration, manager=self)
        self._toasts.append(toast)
        self._reposition()
        toast.animate_in()

    def remove(self, toast):
        if toast in self._toasts:
            self._toasts.remove(toast)
            self._reposition()

    def _reposition(self):
        y = 20
        for toast in reversed(self._toasts):
            toast._target_y = y
            y += 70


class Toast(ctk.CTkFrame):

    TYPE_COLORS = {
        "success": "GREEN",
        "error": "RED",
        "info": "CYAN",
        "warning": "AMBER",
    }

    TYPE_ICONS = {
        "success": "✓",
        "error": "✕",
        "info": "ℹ",
        "warning": "⚠",
    }

    def __init__(self, parent, message: str, toast_type: str = "info",
                 duration: int = 3000, manager: ToastManager = None):
        tm = ThemeManager()
        super().__init__(
            parent,
            fg_color=tm.c("BG_ELEVATED"),
            corner_radius=RADIUS,
            border_width=1,
            border_color=tm.c("BORDER"),
        )

        self._message = message
        self._type = toast_type
        self._duration = duration
        self._manager = manager
        self._target_y = 20
        self._alpha = 0.0

        color_key = self.TYPE_COLORS.get(toast_type, "CYAN")
        accent_color = tm.c(color_key)
        icon = self.TYPE_ICONS.get(toast_type, "ℹ")

        self.configure(width=340, height=56)

        strip = ctk.CTkFrame(self, width=4, height=48, fg_color=accent_color,
                             corner_radius=2)
        strip.place(x=6, y=4)

        icon_label = ctk.CTkLabel(
            self, text=icon, font=(tm.c.__self__.__class__.__name__ and "Helvetica Neue", 16, "bold"),
            text_color=accent_color, width=24,
        )
        icon_label.place(x=18, y=8)

        msg_label = ctk.CTkLabel(
            self, text=message, font=BODY,
            text_color=tm.c("TEXT_PRIMARY"),
            anchor="w", wraplength=260,
        )
        msg_label.place(x=46, y=8)

        type_label = ctk.CTkLabel(
            self, text=toast_type.upper(), font=SMALL,
            text_color=tm.c("TEXT_MUTED"),
        )
        type_label.place(x=46, y=32)

        close_btn = ctk.CTkButton(
            self, text="✕", width=24, height=24,
            fg_color="transparent", hover_color=tm.c("BG_HOVER"),
            text_color=tm.c("TEXT_MUTED"), font=SMALL,
            command=self._dismiss,
        )
        close_btn.place(x=306, y=4)

        self._current_x = parent.winfo_width() + 50
        self.place(x=self._current_x, y=self._target_y)

    def animate_in(self):
        target_x = self.master.winfo_width() - 360
        self._slide_to(target_x, self._target_y, steps=8, then=self._schedule_dismiss)

    def _schedule_dismiss(self):
        self.after(self._duration, self._animate_out)

    def _animate_out(self):
        target_x = self.master.winfo_width() + 50
        self._slide_to(target_x, self._target_y, steps=6, then=self._destroy)

    def _dismiss(self):
        self._animate_out()

    def _slide_to(self, target_x, target_y, steps=8, then=None):
        try:
            info = self.place_info()
            current_x = int(info.get("x", 0))
            current_y = int(info.get("y", 0))
        except Exception:
            current_x = self._current_x
            current_y = self._target_y

        dx = (target_x - current_x) / steps
        dy = (target_y - current_y) / steps
        self._animate_step(current_x, current_y, dx, dy, steps, then)

    def _animate_step(self, x, y, dx, dy, remaining, then):
        if remaining <= 0:
            if then:
                then()
            return
        x += dx
        y += dy
        try:
            self.place(x=int(x), y=int(y))
            self._current_x = int(x)
        except Exception:
            return
        self.after(12, lambda: self._animate_step(x, y, dx, dy, remaining - 1, then))

    def _destroy(self):
        if self._manager:
            self._manager.remove(self)
        try:
            self.destroy()
        except Exception:
            pass
