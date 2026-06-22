import customtkinter as ctk
from gui.theme import ThemeManager, H3, BODY, SMALL, PAD_SM, PAD_MD, PAD_LG, TOPBAR_H


class TopBar(ctk.CTkFrame):

    def __init__(self, parent, on_search=None, on_new_tournament=None,
                 on_bell_click=None):
        tm = ThemeManager()
        super().__init__(
            parent, fg_color=tm.c("BG_SURFACE"),
            height=TOPBAR_H, corner_radius=0,
            border_width=0,
        )
        self.pack_propagate(False)

        self._tm = tm
        self._on_search = on_search
        self._on_bell_click_cb = on_bell_click
        self._notification_count = 0

        border = ctk.CTkFrame(self, height=1, fg_color=tm.c("BORDER"))
        border.place(relx=0, rely=1.0, relwidth=1.0, anchor="sw")

        breadcrumb_frame = ctk.CTkFrame(self, fg_color="transparent")
        breadcrumb_frame.pack(side="left", padx=PAD_LG, pady=PAD_MD)

        self._breadcrumb_root = ctk.CTkLabel(
            breadcrumb_frame, text="EsportsHub",
            font=H3, text_color=tm.c("TEXT_MUTED"),
        )
        self._breadcrumb_root.pack(side="left")

        self._breadcrumb_sep = ctk.CTkLabel(
            breadcrumb_frame, text="  ›  ",
            font=H3, text_color=tm.c("TEXT_MUTED"),
        )
        self._breadcrumb_sep.pack(side="left")

        self._breadcrumb_current = ctk.CTkLabel(
            breadcrumb_frame, text="Dashboard",
            font=H3, text_color=tm.c("TEXT_PRIMARY"),
        )
        self._breadcrumb_current.pack(side="left")

        self._search_entry = ctk.CTkEntry(
            self, width=300, height=36,
            placeholder_text="Search teams, matches…",
            fg_color=tm.c("BG_ELEVATED"),
            border_color=tm.c("BORDER"),
            text_color=tm.c("TEXT_PRIMARY"),
            placeholder_text_color=tm.c("TEXT_MUTED"),
            font=BODY, corner_radius=8,
        )
        self._search_entry.pack(side="left", padx=PAD_LG, expand=True)
        self._search_entry.bind("<Return>", self._do_search)

        right_frame = ctk.CTkFrame(self, fg_color="transparent")
        right_frame.pack(side="right", padx=PAD_LG, pady=PAD_MD)

        if on_new_tournament:
            new_btn = ctk.CTkButton(
                right_frame, text="+ New Tournament", width=140, height=32,
                fg_color=tm.c("ACCENT"), hover_color=tm.c("ACCENT_HOVER"),
                text_color="#FFFFFF", font=SMALL, corner_radius=8,
                command=on_new_tournament,
            )
            new_btn.pack(side="right", padx=(PAD_SM, 0))

        self._notif_frame = ctk.CTkFrame(right_frame, fg_color="transparent",
                                          width=40, height=32)
        self._notif_frame.pack(side="right", padx=(0, PAD_SM))
        self._notif_frame.pack_propagate(False)

        self._bell_btn = ctk.CTkButton(
            self._notif_frame, text="🔔", width=32, height=32,
            fg_color="transparent", hover_color=tm.c("BG_HOVER"),
            text_color=tm.c("TEXT_SECONDARY"), font=("Helvetica", 16),
            corner_radius=8, command=self._on_bell_click,
        )
        self._bell_btn.pack(side="left")

        self._badge = ctk.CTkLabel(
            self._notif_frame, text="0", font=("Helvetica", 9, "bold"),
            text_color="#FFFFFF", fg_color=tm.c("RED"),
            corner_radius=8, width=18, height=18,
        )
        self._badge_visible = False

    def set_breadcrumb(self, view_name: str):
        display_names = {
            "dashboard": "Dashboard",
            "teams": "Teams",
            "matches": "Matches",
            "bracket": "Bracket",
            "rankings": "Rankings",
            "settings": "Settings",
        }
        self._breadcrumb_current.configure(
            text=display_names.get(view_name, view_name.title())
        )

    def update_notification_badge(self, count: int):
        self._notification_count = count
        if count > 0:
            self._badge.configure(text=str(min(count, 99)))
            if not self._badge_visible:
                self._badge.place(x=22, y=0)
                self._badge_visible = True
        else:
            if self._badge_visible:
                self._badge.place_forget()
                self._badge_visible = False

    def _do_search(self, event=None):
        query = self._search_entry.get().strip()
        if self._on_search and query:
            self._on_search(query)

    def _on_bell_click(self):
        self._notification_count = 0
        self.update_notification_badge(0)
        if self._on_bell_click_cb:
            self._on_bell_click_cb()

    def get_search_query(self) -> str:
        return self._search_entry.get().strip()
