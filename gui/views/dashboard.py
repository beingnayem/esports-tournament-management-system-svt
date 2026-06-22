import customtkinter as ctk
from gui.theme import ThemeManager, H1, H2, H3, BODY, SMALL, PAD_SM, PAD_MD, PAD_LG, PAD_XL, RADIUS

try:
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


class DashboardView(ctk.CTkFrame):

    def __init__(self, parent, service=None, app=None):
        tm = ThemeManager()
        super().__init__(parent, fg_color=tm.c("BG_BASE"), corner_radius=0)

        self._tm = tm
        self._service = service
        self.app = app
        self._stat_cards = {}
        self._match_cards = []
        self._chart_canvas = None

        container = ctk.CTkScrollableFrame(
            self, fg_color=tm.c("BG_BASE"), corner_radius=0,
        )
        container.pack(fill="both", expand=True, padx=PAD_LG, pady=PAD_MD)

        title = ctk.CTkLabel(
            container, text="Dashboard", font=H1,
            text_color=tm.c("TEXT_PRIMARY"), anchor="w",
        )
        title.pack(fill="x", pady=(0, PAD_MD))

        stats_frame = ctk.CTkFrame(container, fg_color="transparent")
        stats_frame.pack(fill="x", pady=(0, PAD_LG))

        stats_frame.columnconfigure((0, 1, 2, 3), weight=1)

        from gui.components.stat_card import StatCard

        stats_data = [
            ("active_tournaments", "Active Tournaments", 0, "🏆", tm.c("ACCENT")),
            ("total_teams", "Registered Teams", 0, "👥", tm.c("CYAN")),
            ("matches_today", "Matches Today", 0, "⚔", tm.c("GREEN")),
            ("pending_results", "Pending Results", 0, "⏳", tm.c("AMBER")),
        ]

        for i, (key, label, value, icon, color) in enumerate(stats_data):
            card = StatCard(stats_frame, label=label, value=value,
                           icon=icon, color=color)
            card.grid(row=0, column=i, padx=PAD_SM, sticky="nsew")
            self._stat_cards[key] = card
            
            def make_stat_click(k=key):
                return lambda e: self._on_stat_card_click(k)
            card.bind("<Button-1>", make_stat_click())
            for child in card.winfo_children():
                child.bind("<Button-1>", make_stat_click())
                for subchild in child.winfo_children():
                    subchild.bind("<Button-1>", make_stat_click())

        tournaments_panel = ctk.CTkFrame(container, fg_color=tm.c("BG_SURFACE"),
                                           corner_radius=RADIUS)
        tournaments_panel.pack(fill="x", pady=(0, PAD_LG))

        tournaments_header = ctk.CTkLabel(
            tournaments_panel, text="Created / Active Tournaments", font=H3,
            text_color=tm.c("TEXT_PRIMARY")
        )
        tournaments_header.pack(anchor="w", padx=PAD_MD, pady=(PAD_MD, PAD_SM))

        self._tournaments_container = ctk.CTkScrollableFrame(
            tournaments_panel, fg_color="transparent", height=100, orientation="horizontal"
        )
        self._tournaments_container.pack(fill="x", padx=PAD_SM, pady=(0, PAD_SM))

        row2 = ctk.CTkFrame(container, fg_color="transparent")
        row2.pack(fill="both", expand=True, pady=(0, PAD_LG))
        row2.columnconfigure(0, weight=3)
        row2.columnconfigure(1, weight=2)

        live_panel = ctk.CTkFrame(row2, fg_color=tm.c("BG_SURFACE"),
                                   corner_radius=RADIUS)
        live_panel.grid(row=0, column=0, padx=(0, PAD_SM), sticky="nsew")

        live_header = ctk.CTkFrame(live_panel, fg_color="transparent")
        live_header.pack(fill="x", padx=PAD_MD, pady=PAD_MD)

        self._pulse_dot = ctk.CTkLabel(
            live_header, text="●", font=("Helvetica", 12),
            text_color=tm.c("GREEN"),
        )
        self._pulse_dot.pack(side="left", padx=(0, PAD_SM))

        live_label = ctk.CTkLabel(
            live_header, text="Live Now", font=H3,
            text_color=tm.c("TEXT_PRIMARY"),
        )
        live_label.pack(side="left")

        self._live_container = ctk.CTkScrollableFrame(
            live_panel, fg_color="transparent", height=220,
        )
        self._live_container.pack(fill="both", expand=True, padx=PAD_SM, pady=(0, PAD_SM))

        self._pulse_visible = True
        self._animate_pulse()

        activity_panel = ctk.CTkFrame(row2, fg_color=tm.c("BG_SURFACE"),
                                       corner_radius=RADIUS)
        activity_panel.grid(row=0, column=1, padx=(PAD_SM, 0), sticky="nsew")

        activity_header = ctk.CTkLabel(
            activity_panel, text="Recent Activity", font=H3,
            text_color=tm.c("TEXT_PRIMARY"),
        )
        activity_header.pack(fill="x", padx=PAD_MD, pady=PAD_MD, anchor="w")

        self._activity_feed = ctk.CTkScrollableFrame(
            activity_panel, fg_color="transparent", height=220,
        )
        self._activity_feed.pack(fill="both", expand=True, padx=PAD_SM, pady=(0, PAD_SM))

        chart_panel = ctk.CTkFrame(container, fg_color=tm.c("BG_SURFACE"),
                                    corner_radius=RADIUS, height=300)
        chart_panel.pack(fill="x", pady=(0, PAD_LG))
        chart_panel.pack_propagate(False)

        chart_header = ctk.CTkLabel(
            chart_panel, text="Top 8 Teams by Points", font=H3,
            text_color=tm.c("TEXT_PRIMARY"),
        )
        chart_header.pack(fill="x", padx=PAD_MD, pady=(PAD_MD, 0), anchor="w")

        self._chart_frame = ctk.CTkFrame(chart_panel, fg_color="transparent")
        self._chart_frame.pack(fill="both", expand=True, padx=PAD_SM, pady=PAD_SM)

    def refresh(self):
        if not self._service:
            return

        stats = self._service.get_stats()
        for key, card in self._stat_cards.items():
            if key in stats:
                card.animate_to(stats[key])

        self._refresh_tournaments()

        self._refresh_live_matches()

        self._refresh_activity_feed()

        self._refresh_chart()

    def _refresh_live_matches(self):
        for widget in self._live_container.winfo_children():
            widget.destroy()
        self._match_cards.clear()

        if not self._service:
            return

        from gui.components.match_card import MatchCard

        live = self._service.get_live_matches()
        scheduled = self._service.get_matches_by_status(
            __import__("models.match", fromlist=["MatchStatus"]).MatchStatus.SCHEDULED
        )

        all_matches = live + scheduled[:3]

        if not all_matches:
            empty = ctk.CTkLabel(
                self._live_container, text="No active matches",
                font=BODY, text_color=self._tm.c("TEXT_MUTED"),
            )
            empty.pack(pady=PAD_LG)
            return

        for match in all_matches:
            t1_name = self._service.get_team_name(match.team1_id)
            t2_name = self._service.get_team_name(match.team2_id)
            card = MatchCard(
                self._live_container,
                team1_name=t1_name, team2_name=t2_name,
                score1=match.score1, score2=match.score2,
                status=match.status.value, game=match.game,
                match_id=match.id,
                on_click=self._on_match_click,
            )
            card.pack(fill="x", pady=PAD_SM)
            self._match_cards.append(card)

    def _refresh_activity_feed(self):
        for widget in self._activity_feed.winfo_children():
            widget.destroy()

        if not self._service:
            return

        events = self._service.logging_sub.get_recent(15)
        if not events:
            empty = ctk.CTkLabel(
                self._activity_feed, text="No recent activity",
                font=BODY, text_color=self._tm.c("TEXT_MUTED"),
            )
            empty.pack(pady=PAD_LG)
            return

        for event in reversed(events):
            entry = ctk.CTkFrame(self._activity_feed, fg_color="transparent", height=28)
            entry.pack(fill="x", pady=1)
            entry.pack_propagate(False)

            color = self._tm.c(event.color)
            dot = ctk.CTkLabel(entry, text="●", font=("Helvetica", 8),
                               text_color=color)
            dot.pack(side="left", padx=(PAD_SM, 4))

            time_label = ctk.CTkLabel(
                entry, text=event.timestamp, font=SMALL,
                text_color=self._tm.c("TEXT_MUTED"), width=55,
            )
            time_label.pack(side="left", padx=(0, 4))

            desc_label = ctk.CTkLabel(
                entry, text=event.description, font=SMALL,
                text_color=self._tm.c("TEXT_SECONDARY"), anchor="w",
            )
            desc_label.pack(side="left", fill="x", expand=True)

    def _refresh_chart(self):
        if not HAS_MATPLOTLIB or not self._service:
            return

        for widget in self._chart_frame.winfo_children():
            widget.destroy()

        tm = self._tm
        teams = sorted(self._service.get_all_teams(),
                       key=lambda t: t.points, reverse=True)[:8]

        if not teams:
            return

        fig = Figure(figsize=(8, 2.5), dpi=100)
        fig.patch.set_facecolor(tm.c("BG_SURFACE"))
        ax = fig.add_subplot(111)
        ax.set_facecolor(tm.c("BG_SURFACE"))

        names = [t.tag for t in teams]
        points = [t.points for t in teams]

        bars = ax.bar(names, points, color=tm.c("ACCENT"), width=0.6,
                       edgecolor=tm.c("ACCENT_DIM"), linewidth=0.5)

        ax.set_ylabel("Points", color=tm.c("TEXT_SECONDARY"), fontsize=9)
        ax.tick_params(colors=tm.c("TEXT_SECONDARY"), labelsize=8)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["bottom"].set_color(tm.c("BORDER"))
        ax.spines["left"].set_color(tm.c("BORDER"))

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, self._chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self._chart_canvas = canvas

    def add_activity_event(self, event):
        tm = self._tm
        entry = ctk.CTkFrame(self._activity_feed, fg_color="transparent", height=28)
        entry.pack(fill="x", pady=1)
        entry.pack_propagate(False)

        color = tm.c(event.color)
        dot = ctk.CTkLabel(entry, text="●", font=("Helvetica", 8),
                           text_color=color)
        dot.pack(side="left", padx=(PAD_SM, 4))

        time_label = ctk.CTkLabel(
            entry, text=event.timestamp, font=SMALL,
            text_color=tm.c("TEXT_MUTED"), width=55,
        )
        time_label.pack(side="left", padx=(0, 4))

        desc_label = ctk.CTkLabel(
            entry, text=event.description, font=SMALL,
            text_color=tm.c("TEXT_SECONDARY"), anchor="w",
        )
        desc_label.pack(side="left", fill="x", expand=True)

    def _animate_pulse(self):
        try:
            self._pulse_visible = not self._pulse_visible
            color = self._tm.c("GREEN") if self._pulse_visible else self._tm.c("BG_SURFACE")
            self._pulse_dot.configure(text_color=color)
            self.after(800, self._animate_pulse)
        except Exception:
            pass

    def _on_stat_card_click(self, key):
        if not self.app:
            return
        if key == "total_teams":
            self.app.show_view("teams")
        elif key in ("matches_today", "pending_results"):
            self.app.show_view("matches")
        elif key == "active_tournaments":
            self.app.show_view("bracket")

    def _on_match_click(self, match_id):
        if self.app:
            self.app.show_view("matches")
            matches_view = self.app._views.get("matches")
            if matches_view:
                matches_view.select_match(match_id)

    def _on_tournament_click(self, tournament_id):
        if self._service:
            self._service.switch_tournament(tournament_id)
            if self.app:
                from gui.components.toast import ToastManager
                toast = ToastManager()
                toast.show(f"Switched to tournament: {self._service.tournament_name}", "success")
                self.app.refresh_current_view()

    def _refresh_tournaments(self):
        for widget in self._tournaments_container.winfo_children():
            widget.destroy()

        if not self._service or not hasattr(self._service, "tournaments"):
            return

        tm = self._tm
        for t_id, t in self._service.tournaments.items():
            is_active = (t_id == self._service.active_tournament_id)
            bg_color = tm.c("BG_SELECTED") if is_active else tm.c("BG_SURFACE")
            border_color = tm.c("ACCENT") if is_active else tm.c("BORDER")

            card = ctk.CTkFrame(
                self._tournaments_container, fg_color=bg_color,
                border_width=1, border_color=border_color,
                width=240, height=80
            )
            card.pack(side="left", padx=PAD_SM, pady=2)
            card.pack_propagate(False)

            title_lbl = ctk.CTkLabel(
                card, text=t["name"], font=H3,
                text_color=tm.c("TEXT_PRIMARY"), anchor="w"
            )
            title_lbl.pack(fill="x", padx=PAD_MD, pady=(PAD_SM, 2))

            sub_lbl = ctk.CTkLabel(
                card, text=f"{t['game']} • {t['max_teams']} Teams", font=SMALL,
                text_color=tm.c("TEXT_SECONDARY"), anchor="w"
            )
            sub_lbl.pack(fill="x", padx=PAD_MD)

            status_text = "ACTIVE" if t["tournament_started"] else "CREATED"
            status_color = tm.c("GREEN") if t["tournament_started"] else tm.c("TEXT_MUTED")
            status_lbl = ctk.CTkLabel(
                card, text=status_text, font=SMALL,
                text_color=status_color, anchor="w"
            )
            status_lbl.pack(fill="x", padx=PAD_MD, pady=(2, PAD_SM))

            def make_click_handler(tid=t_id):
                return lambda e: self._on_tournament_click(tid)

            card.bind("<Button-1>", make_click_handler())
            for child in card.winfo_children():
                child.bind("<Button-1>", make_click_handler())
