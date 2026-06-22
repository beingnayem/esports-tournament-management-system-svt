import customtkinter as ctk
from gui.theme import ThemeManager, H1, H3, SMALL, PAD_SM, PAD_MD, RADIUS


class StatCard(ctk.CTkFrame):

    def __init__(self, parent, label: str = "Metric", value: int = 0,
                 icon: str = "📊", color: str = None, **kwargs):
        tm = ThemeManager()
        super().__init__(
            parent,
            fg_color=tm.c("BG_SURFACE"),
            corner_radius=RADIUS,
            border_width=0,
            **kwargs,
        )

        self._tm = tm
        self._current_value = 0
        self._target_value = value
        self._color = color or tm.c("ACCENT")
        self._label_text = label

        self.configure(height=110)

        icon_frame = ctk.CTkFrame(
            self, width=40, height=40,
            fg_color=tm.c("ACCENT_DIM"),
            corner_radius=8,
        )
        icon_frame.place(x=PAD_MD, y=PAD_MD)
        icon_frame.pack_propagate(False)

        icon_label = ctk.CTkLabel(
            icon_frame, text=icon, font=("Helvetica Neue", 18),
            text_color=self._color,
        )
        icon_label.place(relx=0.5, rely=0.5, anchor="center")

        self._value_label = ctk.CTkLabel(
            self, text=str(value), font=H1,
            text_color=tm.c("TEXT_PRIMARY"),
        )
        self._value_label.place(x=PAD_MD, y=58)

        self._label = ctk.CTkLabel(
            self, text=label, font=SMALL,
            text_color=tm.c("TEXT_SECONDARY"),
        )
        self._label.place(x=PAD_MD, y=86)

        bottom_bar = ctk.CTkFrame(
            self, height=2, fg_color=self._color,
            corner_radius=0,
        )
        bottom_bar.place(x=0, rely=1.0, relwidth=1.0, anchor="sw")

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

        if value > 0:
            self._current_value = 0
            self._animate_value()

    def _on_enter(self, event=None):
        self.configure(fg_color=self._tm.c("BG_HOVER"))

    def _on_leave(self, event=None):
        self.configure(fg_color=self._tm.c("BG_SURFACE"))

    def animate_to(self, new_value: int):
        self._target_value = new_value
        self._animate_value()

    def _animate_value(self):
        diff = self._target_value - self._current_value
        if diff == 0:
            return

        steps = 20
        increment = diff / steps
        self._do_count_step(increment, steps)

    def _do_count_step(self, increment, remaining):
        if remaining <= 0:
            self._current_value = self._target_value
            self._value_label.configure(text=str(self._target_value))
            return

        self._current_value += increment
        self._value_label.configure(text=str(int(self._current_value)))
        self.after(25, lambda: self._do_count_step(increment, remaining - 1))

    def set_value(self, value: int, animate: bool = True):
        if animate:
            self.animate_to(value)
        else:
            self._current_value = value
            self._target_value = value
            self._value_label.configure(text=str(value))
