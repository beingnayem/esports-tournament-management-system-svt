import tkinter as tk
import customtkinter as ctk
from gui.theme import ThemeManager, BODY, SMALL, H3, PAD_MD, PAD_SM, RADIUS


class BracketCanvas(ctk.CTkFrame):

    MATCH_W = 180
    MATCH_H = 60
    H_GAP = 80
    V_GAP = 20

    def __init__(self, parent, on_match_click=None, **kwargs):
        tm = ThemeManager()
        super().__init__(parent, fg_color=tm.c("BG_BASE"), **kwargs)

        self._tm = tm
        self._on_match_click = on_match_click
        self._bracket_data = []

        self.canvas = tk.Canvas(
            self, bg=tm.c("BG_BASE"),
            highlightthickness=0, relief="flat",
        )
        h_scroll = ctk.CTkScrollbar(self, orientation="horizontal",
                                     command=self.canvas.xview)
        v_scroll = ctk.CTkScrollbar(self, orientation="vertical",
                                     command=self.canvas.yview)

        self.canvas.configure(xscrollcommand=h_scroll.set,
                               yscrollcommand=v_scroll.set)

        h_scroll.pack(side="bottom", fill="x")
        v_scroll.pack(side="right", fill="y")
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Shift-MouseWheel>", self._on_shift_mousewheel)
        self.canvas.bind("<Button-4>", lambda e: self.canvas.yview_scroll(-1, "units"))
        self.canvas.bind("<Button-5>", lambda e: self.canvas.yview_scroll(1, "units"))
        self.canvas.bind("<Shift-Button-4>", lambda e: self.canvas.xview_scroll(-1, "units"))
        self.canvas.bind("<Shift-Button-5>", lambda e: self.canvas.xview_scroll(1, "units"))

        self._match_rects = {}

    def draw_bracket(self, bracket_data: list):
        self._bracket_data = bracket_data
        self.canvas.delete("all")
        self._match_rects.clear()

        if not bracket_data:
            self._draw_empty()
            return

        tm = self._tm
        num_rounds = len(bracket_data)

        max_matches = max(len(r["matches"]) for r in bracket_data) if bracket_data else 0
        canvas_w = num_rounds * (self.MATCH_W + self.H_GAP) + self.H_GAP
        canvas_h = max_matches * (self.MATCH_H + self.V_GAP) + self.V_GAP + 60

        self.canvas.configure(scrollregion=(0, 0, canvas_w, max(canvas_h, 600)))

        for r_idx, round_data in enumerate(bracket_data):
            x = self.H_GAP + r_idx * (self.MATCH_W + self.H_GAP)
            self.canvas.create_text(
                x + self.MATCH_W // 2, 20,
                text=round_data["name"],
                fill=tm.c("TEXT_SECONDARY"),
                font=H3,
            )

        round_positions = {}
        for r_idx, round_data in enumerate(bracket_data):
            matches = round_data["matches"]
            n_matches = len(matches)
            if n_matches == 0:
                continue

            x = self.H_GAP + r_idx * (self.MATCH_W + self.H_GAP)

            if r_idx == 0:
                total_height = n_matches * (self.MATCH_H + self.V_GAP) - self.V_GAP
                start_y = 50
            else:
                prev_positions = round_positions.get(r_idx - 1, [])
                if len(prev_positions) >= 2:
                    start_y = prev_positions[0][1]
                else:
                    start_y = 50

            positions = []
            for m_idx, match_data in enumerate(matches):
                if r_idx == 0:
                    y = start_y + m_idx * (self.MATCH_H + self.V_GAP)
                else:
                    prev = round_positions.get(r_idx - 1, [])
                    p1_idx = m_idx * 2
                    p2_idx = m_idx * 2 + 1
                    if p2_idx < len(prev):
                        y = (prev[p1_idx][1] + prev[p2_idx][1]) / 2
                    elif p1_idx < len(prev):
                        y = prev[p1_idx][1]
                    else:
                        y = start_y + m_idx * (self.MATCH_H + self.V_GAP)

                cx = x
                cy = y
                positions.append((cx + self.MATCH_W // 2, cy + self.MATCH_H // 2))

                self._draw_match_rect(cx, cy, match_data)

            round_positions[r_idx] = positions

            if r_idx < num_rounds - 1:
                next_x = x + self.MATCH_W + self.H_GAP
                for m_idx in range(0, n_matches, 2):
                    if m_idx + 1 < n_matches:
                        y1 = positions[m_idx][1]
                        y2 = positions[m_idx + 1][1]
                        mid_x = x + self.MATCH_W + self.H_GAP // 2
                        mid_y = (y1 + y2) / 2

                        self.canvas.create_line(
                            x + self.MATCH_W, y1, mid_x, y1,
                            fill=tm.c("BG_HOVER"), width=2,
                        )
                        self.canvas.create_line(
                            x + self.MATCH_W, y2, mid_x, y2,
                            fill=tm.c("BG_HOVER"), width=2,
                        )
                        self.canvas.create_line(
                            mid_x, y1, mid_x, y2,
                            fill=tm.c("BG_HOVER"), width=2,
                        )
                        self.canvas.create_line(
                            mid_x, mid_y, next_x, mid_y,
                            fill=tm.c("BG_HOVER"), width=2,
                        )

    def _draw_match_rect(self, x, y, match_data):
        tm = self._tm
        w = self.MATCH_W
        h = self.MATCH_H

        self._rounded_rect(x, y, x + w, y + h,
                            fill=tm.c("BG_ELEVATED"),
                            outline=tm.c("BORDER"))

        team1 = match_data.get("team1_name", "TBD")
        team2 = match_data.get("team2_name", "TBD")
        winner = match_data.get("winner", None)

        t1_color = tm.c("GREEN") if winner and match_data.get("match") and \
                    match_data["match"].team1_id == winner else tm.c("TEXT_PRIMARY")
        self.canvas.create_text(
            x + 10, y + 18, text=team1, anchor="w",
            fill=t1_color, font=SMALL,
        )

        self.canvas.create_line(x + 5, y + h // 2, x + w - 5, y + h // 2,
                                 fill=tm.c("BORDER"), width=1)

        t2_color = tm.c("GREEN") if winner and match_data.get("match") and \
                    match_data["match"].team2_id == winner else tm.c("TEXT_PRIMARY")
        self.canvas.create_text(
            x + 10, y + h - 18, text=team2, anchor="w",
            fill=t2_color, font=SMALL,
        )

        if match_data.get("match"):
            s1 = str(match_data.get("score1", 0))
            s2 = str(match_data.get("score2", 0))
            self.canvas.create_text(
                x + w - 15, y + 18, text=s1, anchor="e",
                fill=tm.c("TEXT_SECONDARY"), font=SMALL,
            )
            self.canvas.create_text(
                x + w - 15, y + h - 18, text=s2, anchor="e",
                fill=tm.c("TEXT_SECONDARY"), font=SMALL,
            )

        match_id = match_data.get("match_id", "")
        if match_id:
            self._match_rects[(x, y, x + w, y + h)] = match_data

    def _rounded_rect(self, x1, y1, x2, y2, r=8, **kwargs):
        points = [
            x1 + r, y1, x2 - r, y1,
            x2, y1, x2, y1 + r,
            x2, y2 - r, x2, y2,
            x2 - r, y2, x1 + r, y2,
            x1, y2, x1, y2 - r,
            x1, y1 + r, x1, y1,
        ]
        return self.canvas.create_polygon(points, smooth=True, **kwargs)

    def _draw_empty(self):
        tm = self._tm
        self.canvas.create_text(
            self.canvas.winfo_width() // 2 or 400,
            self.canvas.winfo_height() // 2 or 300,
            text="No bracket data.\nStart a tournament to generate the bracket.",
            fill=tm.c("TEXT_MUTED"), font=BODY,
            justify="center",
        )

    def _on_canvas_click(self, event):
        if not self._on_match_click:
            return
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        for (x1, y1, x2, y2), data in self._match_rects.items():
            if x1 <= cx <= x2 and y1 <= cy <= y2:
                match_id = data.get("match_id", "")
                if match_id:
                    self._on_match_click(match_id)
                break

    def export_bracket(self, filepath: str = "bracket.eps"):
        self.canvas.postscript(file=filepath, colormode="color")
        return filepath

    def _on_mousewheel(self, event):
        if event.delta:
            amt = int(-1 * (event.delta / 120))
            if amt == 0:
                amt = -1 if event.delta > 0 else 1
            self.canvas.yview_scroll(amt, "units")

    def _on_shift_mousewheel(self, event):
        if event.delta:
            amt = int(-1 * (event.delta / 120))
            if amt == 0:
                amt = -1 if event.delta > 0 else 1
            self.canvas.xview_scroll(amt, "units")
