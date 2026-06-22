import customtkinter as ctk
from gui.theme import ThemeManager, H1, H3, BODY, SMALL, PAD_SM, PAD_MD, PAD_LG, RADIUS
from gui.components.bracket_canvas import BracketCanvas
from gui.components.toast import ToastManager


class BracketView(ctk.CTkFrame):

    def __init__(self, parent, service=None, bracket_service=None, app=None):
        tm = ThemeManager()
        super().__init__(parent, fg_color=tm.c("BG_BASE"), corner_radius=0)

        self._tm = tm
        self._service = service
        self._bracket_service = bracket_service
        self.app = app

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=PAD_LG, pady=(PAD_MD, PAD_SM))

        title = ctk.CTkLabel(
            header, text="Tournament Bracket", font=H1,
            text_color=tm.c("TEXT_PRIMARY"),
        )
        title.pack(side="left")

        export_btn = ctk.CTkButton(
            header, text="📥 Export Bracket", width=140, height=36,
            fg_color=tm.c("BG_ELEVATED"), hover_color=tm.c("BG_HOVER"),
            text_color=tm.c("TEXT_PRIMARY"), font=SMALL, corner_radius=8,
            border_width=1, border_color=tm.c("BORDER"),
            command=self._export,
        )
        export_btn.pack(side="right")

        self._info_bar = ctk.CTkLabel(
            self, text="", font=SMALL,
            text_color=tm.c("TEXT_SECONDARY"),
        )
        self._info_bar.pack(fill="x", padx=PAD_LG, pady=(0, PAD_SM))

        self._bracket_canvas = BracketCanvas(
            self, on_match_click=self._on_match_click,
        )
        self._bracket_canvas.pack(fill="both", expand=True, padx=PAD_LG, pady=(0, PAD_LG))

    def refresh(self):
        if not self._bracket_service:
            return

        data = self._bracket_service.get_bracket_data()
        self._bracket_canvas.draw_bracket(data)

        total = self._bracket_service.total_rounds
        matches = self._bracket_service.total_matches
        self._info_bar.configure(
            text=f"{total} rounds  •  {matches} matches"
        )

    def _on_match_click(self, match_id: str):
        if self.app:
            self.app.show_view("matches")
            matches_view = self.app._views.get("matches")
            if matches_view:
                matches_view.select_match(match_id)

    def _export(self):
        toast = ToastManager()
        try:
            path = self._bracket_canvas.export_bracket("bracket_export.eps")
            toast.show(f"Bracket exported to {path}", "success")
        except Exception as e:
            toast.show(f"Export failed: {e}", "error")
