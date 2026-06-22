import customtkinter as ctk
from gui.theme import ThemeManager, H2, H3, BODY, SMALL, PAD_SM, PAD_MD, RADIUS


class MatchCard(ctk.CTkFrame):

    STATUS_COLORS = {
        "scheduled": "AMBER",
        "check_in": "CYAN",
        "live": "GREEN",
        "overtime": "ACCENT",
        "completed": "TEXT_MUTED",
        "cancelled": "RED",
        "disputed": "AMBER",
    }

    def __init__(self, parent, team1_name: str = "Team 1",
                 team2_name: str = "Team 2", score1: int = 0,
                 score2: int = 0, status: str = "scheduled",
                 game: str = "CS2", match_id: str = "",
                 on_click=None, **kwargs):
        tm = ThemeManager()
        super().__init__(
            parent, fg_color=tm.c("BG_SURFACE"),
            corner_radius=RADIUS, height=80,
            border_width=1, border_color=tm.c("BORDER"),
            **kwargs,
        )
        self.pack_propagate(False)

        self._tm = tm
        self._match_id = match_id
        self._on_click = on_click
        self._status = status
        self._pulse_state = False

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=PAD_MD, pady=PAD_SM)

        t1_label = ctk.CTkLabel(
            content, text=team1_name, font=H3,
            text_color=tm.c("TEXT_PRIMARY"), anchor="w",
        )
        t1_label.pack(side="left", padx=(0, PAD_SM))

        score_frame = ctk.CTkFrame(content, fg_color="transparent")
        score_frame.pack(side="left", padx=PAD_SM)

        self._score_label = ctk.CTkLabel(
            score_frame, text=f"{score1}  —  {score2}",
            font=H2, text_color=tm.c("TEXT_PRIMARY"),
        )
        self._score_label.pack()

        t2_label = ctk.CTkLabel(
            content, text=team2_name, font=H3,
            text_color=tm.c("TEXT_PRIMARY"), anchor="e",
        )
        t2_label.pack(side="left", padx=(PAD_SM, 0))

        right_frame = ctk.CTkFrame(content, fg_color="transparent")
        right_frame.pack(side="right")

        color_key = self.STATUS_COLORS.get(status, "TEXT_MUTED")
        status_color = tm.c(color_key)

        self._status_badge = ctk.CTkLabel(
            right_frame, text=status.upper(),
            font=SMALL, text_color=status_color,
            fg_color=tm.c("BG_ELEVATED"),
            corner_radius=4, padx=8, pady=2,
        )
        self._status_badge.pack(anchor="e", pady=(0, 2))

        game_chip = ctk.CTkLabel(
            right_frame, text=game, font=SMALL,
            text_color=tm.c("TEXT_MUTED"),
            fg_color=tm.c("BG_ELEVATED"),
            corner_radius=4, padx=6, pady=1,
        )
        game_chip.pack(anchor="e")

        if status in ("live", "overtime"):
            self._dot_label = ctk.CTkLabel(
                right_frame, text="●", font=("Helvetica", 10),
                text_color=status_color,
            )
            self._dot_label.pack(side="right", padx=(PAD_SM, 0))
            self._start_pulse(status_color, tm.c("BG_SURFACE"))

        if on_click:
            self.bind("<Button-1>", lambda e: on_click(match_id))
            for child in self.winfo_children():
                child.bind("<Button-1>", lambda e: on_click(match_id))

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, event=None):
        self.configure(fg_color=self._tm.c("BG_HOVER"))

    def _on_leave(self, event=None):
        self.configure(fg_color=self._tm.c("BG_SURFACE"))

    def update_score(self, score1: int, score2: int):
        self._score_label.configure(text=f"{score1}  —  {score2}")

    def update_status(self, status: str):
        color_key = self.STATUS_COLORS.get(status, "TEXT_MUTED")
        status_color = self._tm.c(color_key)
        self._status_badge.configure(text=status.upper(), text_color=status_color)

    def _start_pulse(self, color_on, color_off):
        if not hasattr(self, '_dot_label'):
            return
        try:
            self._pulse_state = not self._pulse_state
            c = color_on if self._pulse_state else color_off
            self._dot_label.configure(text_color=c)
            self.after(800, lambda: self._start_pulse(color_on, color_off))
        except Exception:
            pass
