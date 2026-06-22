import customtkinter as ctk
from gui.theme import ThemeManager, H1, H2, H3, BODY, SMALL, PAD_SM, PAD_MD, PAD_LG, RADIUS
from gui.components.data_table import DataTable
from gui.components.toast import ToastManager
from gui.components.modal import Modal
from models.match import MatchStatus
from patterns.state import InvalidStateTransitionError


class MatchesView(ctk.CTkFrame):

    STATUS_TABS = ["All", "Scheduled", "Live", "Completed", "Disputed"]
    STATUS_MAP = {
        "Scheduled": MatchStatus.SCHEDULED,
        "Live": MatchStatus.LIVE,
        "Completed": MatchStatus.COMPLETED,
        "Disputed": MatchStatus.DISPUTED,
    }

    def __init__(self, parent, service=None):
        tm = ThemeManager()
        super().__init__(parent, fg_color=tm.c("BG_BASE"), corner_radius=0)

        self._tm = tm
        self._service = service
        self._active_tab = "All"
        self._selected_match_id = None

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=PAD_LG, pady=(PAD_MD, PAD_SM))

        title = ctk.CTkLabel(
            header, text="Matches", font=H1,
            text_color=tm.c("TEXT_PRIMARY"),
        )
        title.pack(side="left")

        create_match_btn = ctk.CTkButton(
            header, text="➕ Create Match", width=140, height=36,
            fg_color=tm.c("ACCENT"), hover_color=tm.c("ACCENT_HOVER"),
            text_color="#FFFFFF", font=SMALL, corner_radius=8,
            command=self._open_create_match,
        )
        create_match_btn.pack(side="right")

        tabs_frame = ctk.CTkFrame(self, fg_color="transparent")
        tabs_frame.pack(fill="x", padx=PAD_LG, pady=(0, PAD_SM))

        self._tab_buttons = {}
        for tab_name in self.STATUS_TABS:
            is_active = tab_name == self._active_tab
            btn = ctk.CTkButton(
                tabs_frame, text=tab_name, width=90, height=30,
                fg_color=tm.c("ACCENT_DIM") if is_active else "transparent",
                hover_color=tm.c("BG_HOVER"),
                text_color=tm.c("ACCENT") if is_active else tm.c("TEXT_SECONDARY"),
                font=SMALL, corner_radius=6,
                command=lambda t=tab_name: self._set_tab(t),
            )
            btn.pack(side="left", padx=2)
            self._tab_buttons[tab_name] = btn

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=PAD_LG, pady=(0, PAD_LG))
        content.columnconfigure(0, weight=1)
        content.columnconfigure(1, weight=0)
        content.rowconfigure(0, weight=1)

        columns = ["Match ID", "Team 1", "Team 2", "Score", "Status", "Game", "Scheduled"]
        col_widths = {"Match ID": 80, "Team 1": 130, "Team 2": 130,
                      "Score": 80, "Status": 90, "Game": 60, "Scheduled": 120}

        self._table = DataTable(
            content, columns=columns, column_widths=col_widths,
            on_select=self._on_match_select,
        )
        self._table.grid(row=0, column=0, sticky="nsew", padx=(0, PAD_SM))

        self._score_panel = ctk.CTkFrame(
            content, fg_color=tm.c("BG_SURFACE"), width=280,
            corner_radius=RADIUS,
        )
        self._score_panel.grid(row=0, column=1, sticky="nsew")
        self._score_panel.pack_propagate(False)

        self._build_score_panel()

    def _build_score_panel(self):
        tm = self._tm
        panel = self._score_panel

        header = ctk.CTkLabel(
            panel, text="Score Updater", font=H3,
            text_color=tm.c("TEXT_PRIMARY"),
        )
        header.pack(fill="x", padx=PAD_MD, pady=PAD_MD)

        sep = ctk.CTkFrame(panel, height=1, fg_color=tm.c("BORDER"))
        sep.pack(fill="x", padx=PAD_SM)

        self._status_label = ctk.CTkLabel(
            panel, text="No match selected", font=SMALL,
            text_color=tm.c("TEXT_MUTED"),
        )
        self._status_label.pack(fill="x", padx=PAD_MD, pady=PAD_SM)

        self._state_badge = ctk.CTkLabel(
            panel, text="—", font=H3,
            text_color=tm.c("TEXT_MUTED"),
            fg_color=tm.c("BG_ELEVATED"),
            corner_radius=6, padx=12, pady=4,
        )
        self._state_badge.pack(pady=PAD_SM)

        score_frame = ctk.CTkFrame(panel, fg_color="transparent")
        score_frame.pack(fill="x", padx=PAD_MD, pady=PAD_SM)

        self._t1_label = ctk.CTkLabel(
            score_frame, text="Team 1", font=BODY,
            text_color=tm.c("TEXT_PRIMARY"),
        )
        self._t1_label.pack(fill="x")

        scores_row = ctk.CTkFrame(score_frame, fg_color="transparent")
        scores_row.pack(fill="x", pady=PAD_SM)

        self._score1_var = ctk.StringVar(value="0")
        self._score1_spin = ctk.CTkEntry(
            scores_row, textvariable=self._score1_var,
            width=60, height=36, font=H2,
            fg_color=tm.c("BG_ELEVATED"), border_color=tm.c("BORDER"),
            text_color=tm.c("TEXT_PRIMARY"), justify="center",
        )
        self._score1_spin.pack(side="left", padx=(0, PAD_SM))

        vs_label = ctk.CTkLabel(scores_row, text="vs", font=H3,
                                text_color=tm.c("TEXT_MUTED"))
        vs_label.pack(side="left", padx=PAD_SM)

        self._score2_var = ctk.StringVar(value="0")
        self._score2_spin = ctk.CTkEntry(
            scores_row, textvariable=self._score2_var,
            width=60, height=36, font=H2,
            fg_color=tm.c("BG_ELEVATED"), border_color=tm.c("BORDER"),
            text_color=tm.c("TEXT_PRIMARY"), justify="center",
        )
        self._score2_spin.pack(side="left", padx=(PAD_SM, 0))

        self._t2_label = ctk.CTkLabel(
            score_frame, text="Team 2", font=BODY,
            text_color=tm.c("TEXT_PRIMARY"),
        )
        self._t2_label.pack(fill="x")

        quick_frame = ctk.CTkFrame(panel, fg_color="transparent")
        quick_frame.pack(fill="x", padx=PAD_MD, pady=PAD_SM)

        self._plus_t1_btn = ctk.CTkButton(
            quick_frame, text="+1 T1", width=80, height=30,
            fg_color=tm.c("BG_ELEVATED"), hover_color=tm.c("BG_HOVER"),
            text_color=tm.c("CYAN"), font=SMALL, corner_radius=6,
            command=lambda: self._increment_score(1),
        )
        self._plus_t1_btn.pack(side="left", padx=2)

        self._plus_t2_btn = ctk.CTkButton(
            quick_frame, text="+1 T2", width=80, height=30,
            fg_color=tm.c("BG_ELEVATED"), hover_color=tm.c("BG_HOVER"),
            text_color=tm.c("CYAN"), font=SMALL, corner_radius=6,
            command=lambda: self._increment_score(2),
        )
        self._plus_t2_btn.pack(side="left", padx=2)

        apply_btn = ctk.CTkButton(
            quick_frame, text="Apply", width=70, height=30,
            fg_color=tm.c("ACCENT"), hover_color=tm.c("ACCENT_HOVER"),
            text_color="#FFFFFF", font=SMALL, corner_radius=6,
            command=self._apply_scores,
        )
        apply_btn.pack(side="left", padx=2)

        sep2 = ctk.CTkFrame(panel, height=1, fg_color=tm.c("BORDER"))
        sep2.pack(fill="x", padx=PAD_SM, pady=PAD_SM)

        self._buttons_frame = ctk.CTkFrame(panel, fg_color="transparent")
        self._buttons_frame.pack(fill="x", padx=PAD_MD, pady=PAD_SM)

        button_configs = [
            ("start_checkin", "Start Check-in", "CYAN"),
            ("start_match", "Start Match", "GREEN"),
            ("overtime", "Overtime", "ACCENT"),
            ("complete", "Complete", "TEXT_MUTED"),
            ("cancel", "Cancel", "RED"),
            ("dispute", "Dispute", "AMBER"),
        ]

        self._action_buttons = {}
        for action, label, color_key in button_configs:
            btn = ctk.CTkButton(
                self._buttons_frame, text=label, height=32,
                fg_color=tm.c("BG_ELEVATED"), hover_color=tm.c("BG_HOVER"),
                text_color=tm.c(color_key), font=SMALL, corner_radius=6,
                border_width=1, border_color=tm.c("BORDER"),
                command=lambda a=action: self._do_action(a),
                state="disabled",
            )
            btn.pack(fill="x", pady=2)
            self._action_buttons[action] = btn

    def refresh(self):
        if not self._service:
            return

        matches = self._service.get_all_matches()

        if self._active_tab != "All":
            status = self.STATUS_MAP.get(self._active_tab)
            if status:
                if self._active_tab == "Live":
                    matches = [m for m in matches if m.is_live]
                else:
                    matches = [m for m in matches if m.status == status]

        rows = []
        for m in matches:
            t1 = self._service.get_team_name(m.team1_id)
            t2 = self._service.get_team_name(m.team2_id)
            score = m.score_display
            rows.append((
                m.id, t1, t2, score,
                m.status.value.upper(), m.game, m.scheduled_time,
            ))

        self._table.set_data(rows)

        if self._selected_match_id:
            self._update_score_panel(self._selected_match_id)

    def _set_tab(self, tab_name: str):
        self._active_tab = tab_name
        tm = self._tm
        for name, btn in self._tab_buttons.items():
            if name == tab_name:
                btn.configure(fg_color=tm.c("ACCENT_DIM"),
                             text_color=tm.c("ACCENT"))
            else:
                btn.configure(fg_color="transparent",
                             text_color=tm.c("TEXT_SECONDARY"))
        self.refresh()

    def _on_match_select(self, row):
        match_id = str(row[0])
        self._selected_match_id = match_id
        self._update_score_panel(match_id)

    def _update_score_panel(self, match_id: str):
        if not self._service:
            return

        match = self._service.get_match(match_id)
        if not match:
            return

        tm = self._tm
        t1 = self._service.get_team_name(match.team1_id)
        t2 = self._service.get_team_name(match.team2_id)

        self._status_label.configure(text=f"Match: {match_id}")
        self._t1_label.configure(text=t1)
        self._t2_label.configure(text=t2)
        self._score1_var.set(str(match.score1))
        self._score2_var.set(str(match.score2))

        ctx = self._service.get_match_context(match_id)
        if ctx:
            state = ctx.state
            color = tm.c(state.color_key)
            self._state_badge.configure(
                text=state.name, text_color=color,
            )

            available = self._service.get_available_actions(match_id)
            for action, btn in self._action_buttons.items():
                if action in available:
                    btn.configure(state="normal")
                else:
                    btn.configure(state="disabled")

    def _increment_score(self, team_num: int):
        if team_num == 1:
            try:
                v = int(self._score1_var.get()) + 1
                self._score1_var.set(str(v))
            except ValueError:
                pass
        else:
            try:
                v = int(self._score2_var.get()) + 1
                self._score2_var.set(str(v))
            except ValueError:
                pass

    def _apply_scores(self):
        if not self._selected_match_id or not self._service:
            return
        toast = ToastManager()
        try:
            s1 = int(self._score1_var.get())
            s2 = int(self._score2_var.get())
            self._service.update_score(self._selected_match_id, s1, s2)
            self.refresh()
            toast.show("Scores updated", "success")
        except Exception as e:
            toast.show(f"Error: {e}", "error")

    def _do_action(self, action: str):
        if not self._selected_match_id or not self._service:
            return
        toast = ToastManager()
        try:
            if action == "complete":
                try:
                    s1 = int(self._score1_var.get())
                    s2 = int(self._score2_var.get())
                    self._service.update_score(self._selected_match_id, s1, s2)
                except ValueError:
                    pass

            self._service.transition_match(self._selected_match_id, action)
            self.refresh()
            toast.show(f"Match state: {action.replace('_', ' ').title()}", "info")
        except InvalidStateTransitionError as e:
            toast.show(str(e), "error")
        except Exception as e:
            toast.show(f"Error: {e}", "error")

    def select_match(self, match_id: str):
        self._set_tab("All")
        for item in self._table.tree.get_children():
            values = self._table.tree.item(item)["values"]
            if values and str(values[0]) == match_id:
                self._table.tree.selection_set(item)
                self._table.tree.see(item)
                self._on_match_select(values)
                break

    def _open_create_match(self):
        if not self._service:
            return
        
        toast = ToastManager()
        teams = self._service.get_all_teams()
        if len(teams) < 2:
            toast.show("Please register at least 2 teams first!", "error")
            return

        def handle_create(t1_id, t2_id, game, round_num, time_str):
            self._service.create_match(
                team1_id=t1_id,
                team2_id=t2_id,
                game=game,
                round_number=round_num,
                scheduled_time=time_str
            )
            self.refresh()
            toast.show("Custom match created!", "success")

        CreateMatchModal(self.winfo_toplevel(), self._service, on_create=handle_create)


class CreateMatchModal(Modal):

    def __init__(self, parent, service, on_create):
        super().__init__(parent, title="Create Custom Match", width=450, height=450)
        self._service = service
        self._on_create = on_create
        tm = ThemeManager()

        self.set_action_text("Create")
        self.set_action_command(self._create)

        teams = service.get_all_teams()
        self.team_map = {f"{t.name} ({t.tag})": t.id for t in teams}
        team_display_names = list(self.team_map.keys())

        ctk.CTkLabel(self.body, text="Team 1", font=SMALL,
                     text_color=tm.c("TEXT_SECONDARY")).pack(anchor="w", pady=(0, 4))
        self._t1_menu = ctk.CTkOptionMenu(
            self.body, values=team_display_names, height=36,
            fg_color=tm.c("BG_ELEVATED"), button_color=tm.c("BG_HOVER"),
            button_hover_color=tm.c("ACCENT_DIM"),
            text_color=tm.c("TEXT_PRIMARY"), font=BODY,
        )
        self._t1_menu.pack(fill="x", pady=(0, PAD_MD))

        ctk.CTkLabel(self.body, text="Team 2", font=SMALL,
                     text_color=tm.c("TEXT_SECONDARY")).pack(anchor="w", pady=(0, 4))
        self._t2_menu = ctk.CTkOptionMenu(
            self.body, values=team_display_names, height=36,
            fg_color=tm.c("BG_ELEVATED"), button_color=tm.c("BG_HOVER"),
            button_hover_color=tm.c("ACCENT_DIM"),
            text_color=tm.c("TEXT_PRIMARY"), font=BODY,
        )
        if len(team_display_names) > 1:
            self._t2_menu.set(team_display_names[1])
        self._t2_menu.pack(fill="x", pady=(0, PAD_MD))

        ctk.CTkLabel(self.body, text="Game Title", font=SMALL,
                     text_color=tm.c("TEXT_SECONDARY")).pack(anchor="w", pady=(0, 4))
        self._game_entry = ctk.CTkEntry(
            self.body, placeholder_text="e.g. CS2",
            fg_color=tm.c("BG_ELEVATED"), border_color=tm.c("BORDER"),
            text_color=tm.c("TEXT_PRIMARY"), font=BODY, height=36,
        )
        self._game_entry.insert(0, service.game or "CS2")
        self._game_entry.pack(fill="x", pady=(0, PAD_MD))

        ctk.CTkLabel(self.body, text="Round Number", font=SMALL,
                     text_color=tm.c("TEXT_SECONDARY")).pack(anchor="w", pady=(0, 4))
        self._round_entry = ctk.CTkEntry(
            self.body, placeholder_text="e.g. 1",
            fg_color=tm.c("BG_ELEVATED"), border_color=tm.c("BORDER"),
            text_color=tm.c("TEXT_PRIMARY"), font=BODY, height=36,
        )
        self._round_entry.insert(0, "1")
        self._round_entry.pack(fill="x", pady=(0, PAD_MD))

        ctk.CTkLabel(self.body, text="Scheduled Time", font=SMALL,
                     text_color=tm.c("TEXT_SECONDARY")).pack(anchor="w", pady=(0, 4))
        from datetime import datetime
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        self._time_entry = ctk.CTkEntry(
            self.body, placeholder_text="YYYY-MM-DD HH:MM",
            fg_color=tm.c("BG_ELEVATED"), border_color=tm.c("BORDER"),
            text_color=tm.c("TEXT_PRIMARY"), font=BODY, height=36,
        )
        self._time_entry.insert(0, now_str)
        self._time_entry.pack(fill="x", pady=(0, PAD_MD))

    def _create(self):
        toast = ToastManager()
        t1_disp = self._t1_menu.get()
        t2_disp = self._t2_menu.get()
        game = self._game_entry.get().strip()
        round_str = self._round_entry.get().strip()
        time_str = self._time_entry.get().strip()

        if not t1_disp or not t2_disp:
            toast.show("Both Team 1 and Team 2 must be selected", "error")
            return

        t1_id = self.team_map.get(t1_disp)
        t2_id = self.team_map.get(t2_disp)

        if t1_id == t2_id:
            toast.show("Team 1 and Team 2 cannot be the same team", "error")
            return

        if not game:
            toast.show("Game title is required", "error")
            return

        try:
            round_num = int(round_str)
        except ValueError:
            toast.show("Round number must be an integer", "error")
            return

        if self._on_create:
            self._on_create(t1_id, t2_id, game, round_num, time_str)
        self.close()
