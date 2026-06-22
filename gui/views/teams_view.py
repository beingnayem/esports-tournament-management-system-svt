import customtkinter as ctk
from gui.theme import ThemeManager, H1, H2, H3, BODY, SMALL, PAD_SM, PAD_MD, PAD_LG, RADIUS
from gui.components.data_table import DataTable
from gui.components.modal import Modal
from gui.components.toast import ToastManager
from models.player import Player, ROLES
from models.team import Team, REGIONS


class TeamsView(ctk.CTkFrame):

    def __init__(self, parent, service=None):
        tm = ThemeManager()
        super().__init__(parent, fg_color=tm.c("BG_BASE"), corner_radius=0)

        self._tm = tm
        self._service = service

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=PAD_LG, pady=(PAD_MD, PAD_SM))

        self._title = ctk.CTkLabel(
            header, text="Teams (0)", font=H1,
            text_color=tm.c("TEXT_PRIMARY"),
        )
        self._title.pack(side="left")

        add_btn = ctk.CTkButton(
            header, text="+ Add Team", width=120, height=36,
            fg_color=tm.c("ACCENT"), hover_color=tm.c("ACCENT_HOVER"),
            text_color="#FFFFFF", font=H3, corner_radius=8,
            command=self._open_add_modal,
        )
        add_btn.pack(side="right")

        filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        filter_frame.pack(fill="x", padx=PAD_LG, pady=(0, PAD_SM))

        ctk.CTkLabel(filter_frame, text="Region:", font=SMALL,
                     text_color=tm.c("TEXT_SECONDARY")).pack(side="left", padx=(0, 4))

        self._region_filter = ctk.CTkOptionMenu(
            filter_frame, values=["All"] + REGIONS, width=100, height=28,
            fg_color=tm.c("BG_ELEVATED"), button_color=tm.c("BG_HOVER"),
            button_hover_color=tm.c("ACCENT_DIM"),
            text_color=tm.c("TEXT_PRIMARY"), font=SMALL,
            command=self._on_filter_change,
        )
        self._region_filter.set("All")
        self._region_filter.pack(side="left", padx=(0, PAD_MD))

        ctk.CTkLabel(filter_frame, text="Sort:", font=SMALL,
                     text_color=tm.c("TEXT_SECONDARY")).pack(side="left", padx=(0, 4))

        self._sort_by = ctk.CTkOptionMenu(
            filter_frame, values=["Name", "Elo", "Wins", "Points"], width=100, height=28,
            fg_color=tm.c("BG_ELEVATED"), button_color=tm.c("BG_HOVER"),
            button_hover_color=tm.c("ACCENT_DIM"),
            text_color=tm.c("TEXT_PRIMARY"), font=SMALL,
            command=self._on_filter_change,
        )
        self._sort_by.set("Elo")
        self._sort_by.pack(side="left")

        columns = ["#", "Tag", "Team Name", "Region", "Roster", "Elo", "W/L", "Actions"]
        col_widths = {"#": 40, "Tag": 70, "Team Name": 160, "Region": 80,
                      "Roster": 60, "Elo": 70, "W/L": 70, "Actions": 100}

        self._table = DataTable(
            self, columns=columns, column_widths=col_widths,
            on_select=self._on_select, on_double_click=self._on_edit,
        )
        self._table.pack(fill="both", expand=True, padx=PAD_LG, pady=(0, PAD_LG))

    def refresh(self):
        if not self._service:
            return

        teams = self._service.get_all_teams()
        self._title.configure(text=f"Teams ({len(teams)})")

        region = self._region_filter.get()
        if region != "All":
            teams = [t for t in teams if t.region == region]

        sort_key = self._sort_by.get()
        sort_map = {
            "Name": lambda t: t.name.lower(),
            "Elo": lambda t: -t.elo,
            "Wins": lambda t: -t.wins,
            "Points": lambda t: -t.points,
        }
        teams.sort(key=sort_map.get(sort_key, lambda t: t.name))

        rows = []
        for i, team in enumerate(teams):
            wl = f"{team.wins}/{team.losses}"
            rows.append((
                i + 1, team.tag, team.name, team.region,
                team.roster_size, round(team.elo, 0), wl, team.id,
            ))

        self._table.set_data(rows)

    def _on_filter_change(self, *args):
        self.refresh()

    def _on_select(self, row):
        pass

    def _on_edit(self, row):
        if not self._service:
            return
        team_id = row[-1]
        team = self._service.get_team(str(team_id))
        if team:
            self._open_edit_modal(team)

    def _open_add_modal(self):
        TeamModal(self.winfo_toplevel(), service=self._service,
                  on_save=self.refresh)

    def _open_edit_modal(self, team: Team):
        TeamModal(self.winfo_toplevel(), service=self._service,
                  team=team, on_save=self.refresh)


class TeamModal(Modal):

    def __init__(self, parent, service=None, team: Team = None,
                 on_save=None):
        title = "Edit Team" if team else "Add Team"
        super().__init__(parent, title=title, width=520, height=640)

        self._service = service
        self._team = team
        self._on_save = on_save
        self._player_rows = []

        tm = ThemeManager()

        self.set_action_text("Save Team")
        self.set_action_command(self._save)

        ctk.CTkLabel(self.body, text="Team Name", font=SMALL,
                     text_color=tm.c("TEXT_SECONDARY")).pack(anchor="w", pady=(0, 4))
        self._name_entry = ctk.CTkEntry(
            self.body, placeholder_text="Enter team name",
            fg_color=tm.c("BG_SURFACE"), border_color=tm.c("BORDER"),
            text_color=tm.c("TEXT_PRIMARY"), font=BODY, height=36,
        )
        self._name_entry.pack(fill="x", pady=(0, PAD_MD))

        ctk.CTkLabel(self.body, text="Tag (max 6 chars)", font=SMALL,
                     text_color=tm.c("TEXT_SECONDARY")).pack(anchor="w", pady=(0, 4))
        self._tag_entry = ctk.CTkEntry(
            self.body, placeholder_text="e.g. NXV",
            fg_color=tm.c("BG_SURFACE"), border_color=tm.c("BORDER"),
            text_color=tm.c("TEXT_PRIMARY"), font=BODY, height=36,
        )
        self._tag_entry.pack(fill="x", pady=(0, PAD_MD))

        ctk.CTkLabel(self.body, text="Region", font=SMALL,
                     text_color=tm.c("TEXT_SECONDARY")).pack(anchor="w", pady=(0, 4))
        self._region_menu = ctk.CTkOptionMenu(
            self.body, values=REGIONS, width=200, height=36,
            fg_color=tm.c("BG_SURFACE"), button_color=tm.c("BG_HOVER"),
            text_color=tm.c("TEXT_PRIMARY"), font=BODY,
        )
        self._region_menu.pack(fill="x", pady=(0, PAD_MD))

        ctk.CTkLabel(self.body, text="Coach", font=SMALL,
                     text_color=tm.c("TEXT_SECONDARY")).pack(anchor="w", pady=(0, 4))
        self._coach_entry = ctk.CTkEntry(
            self.body, placeholder_text="Coach name",
            fg_color=tm.c("BG_SURFACE"), border_color=tm.c("BORDER"),
            text_color=tm.c("TEXT_PRIMARY"), font=BODY, height=36,
        )
        self._coach_entry.pack(fill="x", pady=(0, PAD_MD))

        ctk.CTkLabel(self.body, text="Founded Year", font=SMALL,
                     text_color=tm.c("TEXT_SECONDARY")).pack(anchor="w", pady=(0, 4))
        self._year_entry = ctk.CTkEntry(
            self.body, placeholder_text="2024",
            fg_color=tm.c("BG_SURFACE"), border_color=tm.c("BORDER"),
            text_color=tm.c("TEXT_PRIMARY"), font=BODY, height=36,
        )
        self._year_entry.pack(fill="x", pady=(0, PAD_MD))

        sep = ctk.CTkFrame(self.body, height=1, fg_color=tm.c("BORDER"))
        sep.pack(fill="x", pady=PAD_SM)

        players_header = ctk.CTkFrame(self.body, fg_color="transparent")
        players_header.pack(fill="x", pady=PAD_SM)

        ctk.CTkLabel(players_header, text="Players", font=H3,
                     text_color=tm.c("TEXT_PRIMARY")).pack(side="left")

        add_player_btn = ctk.CTkButton(
            players_header, text="+ Add Player", width=100, height=28,
            fg_color=tm.c("ACCENT_DIM"), hover_color=tm.c("ACCENT"),
            text_color=tm.c("ACCENT"), font=SMALL, corner_radius=6,
            command=self._add_player_row,
        )
        add_player_btn.pack(side="right")

        self._players_frame = ctk.CTkFrame(self.body, fg_color="transparent")
        self._players_frame.pack(fill="x", pady=PAD_SM)

        if team:
            self._name_entry.insert(0, team.name)
            self._tag_entry.insert(0, team.tag)
            self._region_menu.set(team.region)
            self._coach_entry.insert(0, team.coach)
            self._year_entry.insert(0, str(team.founded_year))
            for player in team.players:
                self._add_player_row(player)
        else:
            self._add_player_row()

    def _add_player_row(self, player: Player = None):
        tm = ThemeManager()
        row = ctk.CTkFrame(self._players_frame, fg_color=tm.c("BG_SURFACE"),
                           corner_radius=6, height=40)
        row.pack(fill="x", pady=2)
        row.pack_propagate(False)

        name_entry = ctk.CTkEntry(
            row, placeholder_text="Username", width=130, height=30,
            fg_color=tm.c("BG_ELEVATED"), border_color=tm.c("BORDER"),
            text_color=tm.c("TEXT_PRIMARY"), font=SMALL,
        )
        name_entry.pack(side="left", padx=4, pady=4)

        role_menu = ctk.CTkOptionMenu(
            row, values=ROLES, width=90, height=30,
            fg_color=tm.c("BG_ELEVATED"), button_color=tm.c("BG_HOVER"),
            text_color=tm.c("TEXT_PRIMARY"), font=SMALL,
        )
        role_menu.pack(side="left", padx=4)

        age_entry = ctk.CTkEntry(
            row, placeholder_text="Age", width=50, height=30,
            fg_color=tm.c("BG_ELEVATED"), border_color=tm.c("BORDER"),
            text_color=tm.c("TEXT_PRIMARY"), font=SMALL,
        )
        age_entry.pack(side="left", padx=4)

        remove_btn = ctk.CTkButton(
            row, text="✕", width=28, height=28,
            fg_color="transparent", hover_color=tm.c("RED"),
            text_color=tm.c("TEXT_MUTED"), font=SMALL,
            command=lambda: self._remove_player_row(row, entry_data),
        )
        remove_btn.pack(side="right", padx=4)

        entry_data = {"row": row, "name": name_entry, "role": role_menu, "age": age_entry}
        self._player_rows.append(entry_data)

        if player:
            name_entry.insert(0, player.username)
            role_menu.set(player.role)
            age_entry.insert(0, str(player.age))

    def _remove_player_row(self, row, entry_data):
        row.destroy()
        if entry_data in self._player_rows:
            self._player_rows.remove(entry_data)

    def _save(self):
        toast = ToastManager()
        tm = ThemeManager()

        name = self._name_entry.get().strip()
        tag = self._tag_entry.get().strip()
        region = self._region_menu.get()
        coach = self._coach_entry.get().strip()
        year_str = self._year_entry.get().strip()

        if not name:
            toast.show("Team name is required", "error")
            return
        if not tag:
            toast.show("Team tag is required", "error")
            return
        if len(tag) > 6:
            toast.show("Tag must be ≤6 characters", "error")
            return

        try:
            year = int(year_str) if year_str else 2024
        except ValueError:
            toast.show("Invalid founded year", "error")
            return

        players = []
        for entry in self._player_rows:
            try:
                pname = entry["name"].get().strip()
                if not pname:
                    continue
                role = entry["role"].get()
                age_str = entry["age"].get().strip()
                age = int(age_str) if age_str else 18
                players.append(Player(username=pname, role=role, age=age))
            except ValueError as e:
                toast.show(f"Player error: {e}", "error")
                return

        if not players:
            toast.show("At least 1 player is required", "error")
            return

        try:
            if self._team:
                self._team.name = name
                self._team.tag = tag
                self._team.region = region
                self._team.coach = coach
                self._team.founded_year = year
                self._team.players = players
                self._service.update_team(self._team)
                toast.show(f"Team '{name}' updated successfully", "success")
            else:
                team = Team(name=name, tag=tag, region=region,
                           coach=coach, founded_year=year, players=players)
                self._service.register_team(team)
                toast.show(f"Team '{name}' registered successfully", "success")
        except Exception as e:
            toast.show(f"Error: {e}", "error")
            return

        if self._on_save:
            self._on_save()
        self.close()
