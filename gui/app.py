import customtkinter as ctk
import threading
import json
import os
from datetime import datetime, timedelta

from gui.theme import ThemeManager, PAD_SM, PAD_MD, PAD_LG, SIDEBAR_W, RADIUS, H3, H2, BODY, SMALL
from gui.components.sidebar import AnimatedSidebar
from gui.components.topbar import TopBar
from gui.components.toast import ToastManager
from gui.components.modal import Modal
from gui.views.dashboard import DashboardView
from gui.views.teams_view import TeamsView
from gui.views.matches_view import MatchesView
from gui.views.bracket_view import BracketView
from gui.views.rankings_view import RankingsView
from gui.views.settings_view import SettingsView
from services.tournament_service import TournamentService
from services.bracket_service import BracketService
from patterns.observer import ObserverBridge


class EsportsApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("EsportsHub — Tournament Manager")
        self.geometry("1280x800")
        self.minsize(1024, 680)
        self._center_window()

        tm = ThemeManager()
        self.configure(fg_color=tm.c("BG_BASE"))

        self.service = TournamentService()
        self.bracket_service = BracketService(tournament_service=self.service)
        self.service.bracket_sub.set_callback(self._on_bracket_match_completed)

        self._observer_bridge = ObserverBridge(root=self)
        self._observer_bridge.add_gui_callback(self._on_observer_event)
        self.service.set_observer_bridge(self._observer_bridge)

        self._toast_manager = ToastManager()
        self._toast_manager.set_root(self)

        self._current_view_name = "dashboard"
        self._views = {}

        self._build_layout()

        if not self.load_state():
            self._seed_demo_data()

        self.show_view("dashboard")

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _center_window(self):
        self.update_idletasks()
        w = 1280
        h = 800
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build_layout(self):
        tm = ThemeManager()

        main_container = ctk.CTkFrame(self, fg_color=tm.c("BG_BASE"),
                                       corner_radius=0)
        main_container.pack(fill="both", expand=True)

        self.sidebar = AnimatedSidebar(
            main_container, on_navigate=self.show_view,
        )
        self.sidebar.pack(side="left", fill="y")

        right_area = ctk.CTkFrame(main_container, fg_color=tm.c("BG_BASE"),
                                   corner_radius=0)
        right_area.pack(side="left", fill="both", expand=True)

        self.topbar = TopBar(
            right_area,
            on_search=self._on_search,
            on_new_tournament=self._open_new_tournament,
            on_bell_click=self._open_notifications,
        )
        self.topbar.pack(fill="x")

        self._main_frame = ctk.CTkFrame(right_area, fg_color=tm.c("BG_BASE"),
                                          corner_radius=0)
        self._main_frame.pack(fill="both", expand=True)

        self._views["dashboard"] = DashboardView(self._main_frame, service=self.service, app=self)
        self._views["teams"] = TeamsView(self._main_frame, service=self.service)
        self._views["matches"] = MatchesView(self._main_frame, service=self.service)
        self._views["bracket"] = BracketView(self._main_frame, service=self.service,
                                              bracket_service=self.bracket_service, app=self)
        self._views["rankings"] = RankingsView(self._main_frame, service=self.service)
        self._views["settings"] = SettingsView(self._main_frame, service=self.service,
                                                app=self)

    def show_view(self, view_name: str):
        for name, view in self._views.items():
            view.pack_forget()

        if view_name in self._views:
            self._current_view_name = view_name
            self._views[view_name].pack(fill="both", expand=True)
            self._views[view_name].refresh()
            self.topbar.set_breadcrumb(view_name)
            self.sidebar.set_active(view_name)

    def refresh_current_view(self):
        if self._current_view_name in self._views:
            self._views[self._current_view_name].refresh()

    def apply_theme(self):
        tm = ThemeManager()
        self.configure(fg_color=tm.c("BG_BASE"))
        self.refresh_current_view()

    def _on_observer_event(self, event):
        self.topbar.update_notification_badge(
            self.service.notification_sub.unread_count
        )
        dashboard = self._views.get("dashboard")
        if dashboard and self._current_view_name == "dashboard":
            dashboard.add_activity_event(event)

        self.save_state()

    def _on_bracket_match_completed(self, match_id: str):
        match = self.service.get_match(match_id)
        if match and match.winner_id:
            self.bracket_service.advance_winner(match_id, match.winner_id)
            self.refresh_current_view()

    def _on_search(self, query: str):
        results = self.service.search(query)
        toast = ToastManager()
        if results:
            msg = f"Found {len(results)} result(s) for '{query}'"
            toast.show(msg, "info")
            first = results[0]
            if first["type"] == "team":
                self.show_view("teams")
            elif first["type"] == "match":
                self.show_view("matches")
        else:
            toast.show(f"No results for '{query}'", "warning")

    def _open_test_runner(self):
        TestRunnerModal(self)

    def _open_new_tournament(self):
        def handle_create(name, game, type_name, max_teams, seed_demo):
            self.service.create_new_tournament(name, game, type_name, max_teams)
            if seed_demo:
                self._seed_tournament_teams(name, game, type_name, max_teams)
            self.show_view("dashboard")
            toast = ToastManager()
            toast.show(f"Tournament '{name}' created and activated!", "success")
        
        CreateTournamentModal(self, on_create=handle_create)

    def _seed_tournament_teams(self, name, game, type_name, max_teams):
        from models.player import Player
        from models.team import Team

        team_data = [
            ("Nexus Void", "NXV", "EU", "Coach Titan", [
                ("Phantom", "Rifler", 22), ("NightShade", "AWPer", 24),
                ("Blitz", "Entry", 20), ("Sage", "Support", 23), ("Vortex", "IGL", 25),
            ]),
            ("Iron Ghost", "IRON", "NA", "Coach Steel", [
                ("Specter", "IGL", 26), ("Havoc", "Rifler", 21),
                ("Frost", "AWPer", 23), ("Echo", "Support", 22), ("Rush", "Entry", 20),
            ]),
            ("Solar Flare", "SLR", "APAC", "Coach Ray", [
                ("Blaze", "Entry", 19), ("Nova", "AWPer", 22),
                ("Pulse", "Rifler", 21), ("Zen", "IGL", 27), ("Arc", "Support", 20),
            ]),
            ("Dark Horizon", "DH", "EU", "Coach Shadow", [
                ("Reaper", "AWPer", 24), ("Storm", "Rifler", 22),
                ("Cipher", "IGL", 25), ("Dusk", "Entry", 21), ("Raven", "Support", 23),
            ]),
            ("Crystal Edge", "CRYS", "CIS", "Coach Ice", [
                ("Prism", "Rifler", 20), ("Shard", "AWPer", 23),
                ("Glint", "Entry", 19), ("Frost", "IGL", 26), ("Clear", "Support", 22),
            ]),
            ("Omega Rising", "OMEGA", "NA", "Coach Peak", [
                ("Apex", "IGL", 28), ("Bolt", "AWPer", 22),
                ("Strike", "Rifler", 21), ("Guard", "Support", 24), ("Fury", "Entry", 20),
            ]),
            ("Phoenix Core", "PHX", "SA", "Coach Flame", [
                ("Ash", "Entry", 21), ("Ember", "AWPer", 23),
                ("Flare", "Rifler", 22), ("Ignite", "IGL", 25), ("Spark", "Support", 20),
            ]),
            ("Shadow Wolves", "SWLV", "EU", "Coach Fang", [
                ("Alpha", "IGL", 27), ("Howl", "AWPer", 22),
                ("Prowl", "Rifler", 21), ("Claw", "Entry", 19), ("Pack", "Support", 24),
            ]),
        ]

        team_data = team_data[:max_teams]

        teams = []
        for tname, tag, region, coach, players_data in team_data:
            players = [Player(username=pn, role=pr, age=pa) for pn, pr, pa in players_data]
            team = Team(name=tname, tag=tag, region=region, coach=coach,
                        founded_year=2023, players=players)
            self.service.register_team(team)
            teams.append(team)

        self.service.configure_tournament(type_name, name=name, game=game, max_teams=max_teams)
        self.service.start_tournament()

        team_ids = [t.id for t in teams]
        team_names = {t.id: t.name for t in teams}

        def match_factory(t1_id, t2_id, round_num, position):
            return self.service.create_match(t1_id or "", t2_id or "", game, round_num, position)

        self.bracket_service.set_match_factory(match_factory)
        self.bracket_service.generate_bracket(team_ids, team_names)

    def _open_notifications(self):
        notifs = self.service.notification_sub.notifications
        NotificationModal(self, notifs)

    def _on_close(self):
        self.save_state()
        self.destroy()

    def _seed_demo_data(self):
        from models.player import Player
        from models.team import Team
        from models.match import Match, MatchStatus, MatchResult

        team_data = [
            ("Nexus Void", "NXV", "EU", "Coach Titan", [
                ("Phantom", "Rifler", 22), ("NightShade", "AWPer", 24),
                ("Blitz", "Entry", 20), ("Sage", "Support", 23), ("Vortex", "IGL", 25),
            ]),
            ("Iron Ghost", "IRON", "NA", "Coach Steel", [
                ("Specter", "IGL", 26), ("Havoc", "Rifler", 21),
                ("Frost", "AWPer", 23), ("Echo", "Support", 22), ("Rush", "Entry", 20),
            ]),
            ("Solar Flare", "SLR", "APAC", "Coach Ray", [
                ("Blaze", "Entry", 19), ("Nova", "AWPer", 22),
                ("Pulse", "Rifler", 21), ("Zen", "IGL", 27), ("Arc", "Support", 20),
            ]),
            ("Dark Horizon", "DH", "EU", "Coach Shadow", [
                ("Reaper", "AWPer", 24), ("Storm", "Rifler", 22),
                ("Cipher", "IGL", 25), ("Dusk", "Entry", 21), ("Raven", "Support", 23),
            ]),
            ("Crystal Edge", "CRYS", "CIS", "Coach Ice", [
                ("Prism", "Rifler", 20), ("Shard", "AWPer", 23),
                ("Glint", "Entry", 19), ("Frost", "IGL", 26), ("Clear", "Support", 22),
            ]),
            ("Omega Rising", "OMEGA", "NA", "Coach Peak", [
                ("Apex", "IGL", 28), ("Bolt", "AWPer", 22),
                ("Strike", "Rifler", 21), ("Guard", "Support", 24), ("Fury", "Entry", 20),
            ]),
            ("Phoenix Core", "PHX", "SA", "Coach Flame", [
                ("Ash", "Entry", 21), ("Ember", "AWPer", 23),
                ("Flare", "Rifler", 22), ("Ignite", "IGL", 25), ("Spark", "Support", 20),
            ]),
            ("Shadow Wolves", "SWLV", "EU", "Coach Fang", [
                ("Alpha", "IGL", 27), ("Howl", "AWPer", 22),
                ("Prowl", "Rifler", 21), ("Claw", "Entry", 19), ("Pack", "Support", 24),
            ]),
        ]

        teams = []
        for name, tag, region, coach, players_data in team_data:
            players = [Player(username=pn, role=pr, age=pa) for pn, pr, pa in players_data]
            team = Team(name=name, tag=tag, region=region, coach=coach,
                       founded_year=2023, players=players)
            self.service.register_team(team)
            teams.append(team)

        team_ids = [t.id for t in teams]
        team_names = {t.id: t.name for t in teams}

        def match_factory(t1_id, t2_id, round_num, position):
            if not t1_id or not t2_id:
                return self.service.create_match(
                    t1_id or "", t2_id or "", "CS2",
                    round_num, position,
                )
            return self.service.create_match(
                t1_id, t2_id, "CS2", round_num, position,
            )

        self.bracket_service.set_match_factory(match_factory)
        self.bracket_service.generate_bracket(team_ids, team_names)

        matches = list(self.service.matches.values())

        if len(matches) >= 1:
            m = matches[0]
            ctx = self.service.get_match_context(m.id)
            if ctx:
                try:
                    ctx.start_checkin()
                    ctx.start_match()
                    self.service.update_score(m.id, 2, 1)
                    ctx.complete()
                except Exception:
                    pass

        if len(matches) >= 2:
            m = matches[1]
            ctx = self.service.get_match_context(m.id)
            if ctx:
                try:
                    ctx.start_checkin()
                    ctx.start_match()
                    self.service.update_score(m.id, 0, 2)
                    ctx.complete()
                except Exception:
                    pass

        if len(matches) >= 3:
            m = matches[2]
            ctx = self.service.get_match_context(m.id)
            if ctx:
                try:
                    ctx.start_checkin()
                    ctx.start_match()
                    self.service.update_score(m.id, 2, 0)
                    ctx.complete()
                except Exception:
                    pass

        if len(matches) >= 4:
            m = matches[3]
            ctx = self.service.get_match_context(m.id)
            if ctx:
                try:
                    ctx.start_checkin()
                    ctx.start_match()
                    self.service.update_score(m.id, 1, 1)
                except Exception:
                    pass

        for m in matches[:3]:
            if m.winner_id:
                self.bracket_service.advance_winner(m.id, m.winner_id)

        self.service.tournament_name = "EsportsHub Major 2024"
        self.service.tournament_started = True

    def save_state(self):
        try:
            serialized_tournaments = {}
            for t_id, t in self.service.tournaments.items():
                serialized_tournaments[t_id] = {
                    "id": t["id"],
                    "name": t["name"],
                    "game": t["game"],
                    "type_name": t["type_name"],
                    "max_teams": t["max_teams"],
                    "tournament_started": t["tournament_started"],
                    "teams": [team.to_dict() for team in t["teams"].values()],
                    "matches": [match.to_dict() for match in t["matches"].values()],
                }
            state_data = {
                "active_tournament_id": self.service.active_tournament_id,
                "tournaments": serialized_tournaments
            }
            state_file = os.path.join(os.path.dirname(__file__), "..", "app_state.json")
            with open(state_file, "w") as f:
                json.dump(state_data, f, indent=2)
        except Exception as e:
            print("Failed to save state:", e)
    def load_state(self) -> bool:
        state_file = os.path.join(os.path.dirname(__file__), "..", "app_state.json")
        if not os.path.exists(state_file):
            return False
        try:
            with open(state_file, "r") as f:
                state_data = json.load(f)
            
            if "tournament_name" in state_data and "tournaments" not in state_data:
                config_data = state_data.get("config") or {}
                tournaments_data = {
                    "default": {
                        "id": "default",
                        "name": state_data.get("tournament_name", "EsportsHub Tournament"),
                        "game": config_data.get("game", "CS2"),
                        "type_name": config_data.get("type", "Single Elimination"),
                        "max_teams": config_data.get("max_teams", 8),
                        "tournament_started": state_data.get("tournament_started", False),
                        "teams": state_data.get("teams", []),
                        "matches": state_data.get("matches", []),
                    }
                }
                state_data = {
                    "active_tournament_id": "default",
                    "tournaments": tournaments_data
                }

            tournaments_data = state_data.get("tournaments", {})
            if not tournaments_data:
                return False

            from models.team import Team
            from models.match import Match
            from patterns.state import MatchContext

            self.service.tournaments.clear()

            for t_id, t_data in tournaments_data.items():
                teams = {}
                for team_dict in t_data.get("teams", []):
                    team = Team.from_dict(team_dict)
                    teams[team.id] = team

                matches = {}
                match_contexts = {}
                for match_dict in t_data.get("matches", []):
                    match = Match.from_dict(match_dict)
                    matches[match.id] = match
                    ctx = MatchContext(match, initial_state=match.status.value)
                    ctx.set_on_transition(
                        lambda from_s, to_s, mid=match.id: self.service._on_match_state_change(mid, from_s, to_s)
                    )
                    match_contexts[match.id] = ctx

                self.service.tournaments[t_id] = {
                    "id": t_data["id"],
                    "name": t_data["name"],
                    "game": t_data["game"],
                    "type_name": t_data["type_name"],
                    "max_teams": t_data["max_teams"],
                    "teams": teams,
                    "matches": matches,
                    "match_contexts": match_contexts,
                    "config": None,
                    "bracket": None,
                    "tournament_started": t_data["tournament_started"]
                }

            active_id = state_data.get("active_tournament_id", "default")
            if active_id in self.service.tournaments:
                self.service.active_tournament_id = active_id
            else:
                self.service.active_tournament_id = list(self.service.tournaments.keys())[0]

            for t_id, t in self.service.tournaments.items():
                if t["tournament_started"]:
                    prev_active = self.service.active_tournament_id
                    self.service.active_tournament_id = t_id
                    
                    self.service.configure_tournament(
                        t["type_name"], name=t["name"], game=t["game"], max_teams=t["max_teams"]
                    )
                    
                    teams_list = list(t["teams"].values())
                    team_ids = [team.id for team in teams_list]
                    team_names = {team.id: team.name for team in teams_list}
                    
                    def match_lookup_factory(t1_id, t2_id, round_num, position, t_matches=t["matches"]):
                        for m in t_matches.values():
                            if m.round_number == round_num and m.bracket_position == position:
                                return m
                        return Match(team1_id=t1_id or "", team2_id=t2_id or "",
                                     game=t["game"], round_number=round_num, bracket_position=position)

                    try:
                        self.bracket_service.set_match_factory(match_lookup_factory)
                        self.bracket_service.generate_bracket(team_ids, team_names)
                    except Exception as e:
                        print("Failed to rebuild bracket tree:", e)
                    
                    self.service.active_tournament_id = prev_active

            return True
        except Exception as e:
            print("Failed to load state:", e)
            return False
class TestRunnerModal(Modal):

    def __init__(self, parent):
        super().__init__(parent, title="Test Runner", width=700, height=550)

        tm = ThemeManager()
        self.set_action_text("Run Tests")
        self.set_action_command(self._run_tests)

        self._output = ctk.CTkTextbox(
            self.body, font=("Menlo", 11, "normal"),
            fg_color=tm.c("BG_BASE"),
            text_color=tm.c("TEXT_PRIMARY"),
            state="disabled",
        )
        self._output.pack(fill="both", expand=True, pady=(0, PAD_SM))

        self._progress = ctk.CTkProgressBar(
            self.body, fg_color=tm.c("BG_ELEVATED"),
            progress_color=tm.c("ACCENT"),
        )
        self._progress.pack(fill="x", pady=(0, PAD_SM))
        self._progress.set(0)

        self._summary = ctk.CTkLabel(
            self.body, text="Click 'Run Tests' to begin", font=("Menlo", 11),
            text_color=tm.c("TEXT_SECONDARY"),
        )
        self._summary.pack(fill="x")

        self._running = False

    def _run_tests(self):
        if self._running:
            return
        self._running = True

        self._output.configure(state="normal")
        self._output.delete("1.0", "end")
        self._output.configure(state="disabled")
        self._progress.set(0)
        self._summary.configure(text="Running tests...")

        thread = threading.Thread(target=self._execute_tests, daemon=True)
        thread.start()

    def _execute_tests(self):
        import unittest
        import io
        import sys

        loader = unittest.TestLoader()
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        suite = loader.discover(os.path.join(project_dir, "tests"),
                                pattern="test_*.py",
                                top_level_dir=project_dir)

        total = 0
        for group in suite:
            try:
                for test_group in group:
                    try:
                        total += test_group.countTestCases()
                    except Exception:
                        total += 1
            except TypeError:
                total += 1

        if total == 0:
            self.after(0, lambda: self._append_output("No tests found.\n"))
            return

        completed = [0]
        passed = [0]
        failed = [0]
        errors = [0]

        class StreamResult(unittest.TestResult):
            def __init__(self, modal):
                super().__init__()
                self.modal = modal

            def addSuccess(self, test):
                super().addSuccess(test)
                completed[0] += 1
                passed[0] += 1
                self.modal.after(0, lambda t=test: self.modal._append_output(
                    f"  ✓ {t}\n", "green"))
                self.modal.after(0, lambda: self.modal._progress.set(
                    completed[0] / max(total, 1)))

            def addFailure(self, test, err):
                super().addFailure(test, err)
                completed[0] += 1
                failed[0] += 1
                self.modal.after(0, lambda t=test, e=err: self.modal._append_output(
                    f"  ✗ {t}\n    {e[1]}\n", "red"))
                self.modal.after(0, lambda: self.modal._progress.set(
                    completed[0] / max(total, 1)))

            def addError(self, test, err):
                super().addError(test, err)
                completed[0] += 1
                errors[0] += 1
                self.modal.after(0, lambda t=test, e=err: self.modal._append_output(
                    f"  ✗ ERROR {t}\n    {e[1]}\n", "red"))
                self.modal.after(0, lambda: self.modal._progress.set(
                    completed[0] / max(total, 1)))

        self.after(0, lambda: self._append_output(
            f"Discovered {total} tests...\n\n"))

        result = StreamResult(self)
        suite.run(result)

        tm = ThemeManager()
        total_run = passed[0] + failed[0] + errors[0]
        summary = f"{total_run} tests | ✓ {passed[0]} passed | ✗ {failed[0] + errors[0]} failed"
        color = tm.c("GREEN") if failed[0] + errors[0] == 0 else tm.c("RED")
        self.after(0, lambda: self._summary.configure(text=summary, text_color=color))
        self.after(0, lambda: self._progress.set(1.0))
        self._running = False

    def _append_output(self, text: str, color: str = None):
        self._output.configure(state="normal")
        self._output.insert("end", text)
        self._output.see("end")
        self._output.configure(state="disabled")


class CreateTournamentModal(Modal):

    def __init__(self, parent, on_create=None):
        super().__init__(parent, title="Create Tournament", width=500, height=450)
        self._on_create = on_create
        tm = ThemeManager()

        self.set_action_text("Create")
        self.set_action_command(self._create)

        ctk.CTkLabel(self.body, text="Tournament Name", font=SMALL,
                     text_color=tm.c("TEXT_SECONDARY")).pack(anchor="w", pady=(0, 4))
        self._name_entry = ctk.CTkEntry(
            self.body, placeholder_text="e.g. ESL Pro League Season 20",
            fg_color=tm.c("BG_SURFACE"), border_color=tm.c("BORDER"),
            text_color=tm.c("TEXT_PRIMARY"), font=BODY, height=36,
        )
        self._name_entry.pack(fill="x", pady=(0, PAD_MD))

        ctk.CTkLabel(self.body, text="Game Title", font=SMALL,
                     text_color=tm.c("TEXT_SECONDARY")).pack(anchor="w", pady=(0, 4))
        self._game_entry = ctk.CTkEntry(
            self.body, placeholder_text="e.g. CS2, Valorant",
            fg_color=tm.c("BG_SURFACE"), border_color=tm.c("BORDER"),
            text_color=tm.c("TEXT_PRIMARY"), font=BODY, height=36,
        )
        self._game_entry.insert(0, "CS2")
        self._game_entry.pack(fill="x", pady=(0, PAD_MD))

        ctk.CTkLabel(self.body, text="Tournament Type", font=SMALL,
                     text_color=tm.c("TEXT_SECONDARY")).pack(anchor="w", pady=(0, 4))
        from patterns.factory import TournamentFactory
        types = TournamentFactory.available_types()
        self._type_menu = ctk.CTkOptionMenu(
            self.body, values=types, width=250, height=36,
            fg_color=tm.c("BG_SURFACE"), button_color=tm.c("BG_HOVER"),
            text_color=tm.c("TEXT_PRIMARY"), font=BODY,
        )
        self._type_menu.set("Single Elimination")
        self._type_menu.pack(fill="x", pady=(0, PAD_MD))

        ctk.CTkLabel(self.body, text="Max Teams", font=SMALL,
                     text_color=tm.c("TEXT_SECONDARY")).pack(anchor="w", pady=(0, 4))

        slider_frame = ctk.CTkFrame(self.body, fg_color="transparent")
        slider_frame.pack(fill="x", pady=(0, PAD_MD))

        self._max_teams_var = ctk.IntVar(value=8)
        self._max_teams_label = ctk.CTkLabel(
            slider_frame, text="8", font=H3,
            text_color=tm.c("ACCENT"), width=40,
        )
        self._max_teams_label.pack(side="right")

        self._max_teams_slider = ctk.CTkSlider(
            slider_frame, from_=4, to=32,
            number_of_steps=14,
            variable=self._max_teams_var,
            fg_color=tm.c("BG_SURFACE"),
            progress_color=tm.c("ACCENT"),
            button_color=tm.c("ACCENT"),
            button_hover_color=tm.c("ACCENT_HOVER"),
            command=self._on_slider_change,
        )
        self._max_teams_slider.pack(fill="x", side="left", expand=True, padx=(0, PAD_SM))

        self._seed_var = ctk.BooleanVar(value=True)
        self._seed_cb = ctk.CTkCheckBox(
            self.body, text="Seed with Demo Teams & Start",
            variable=self._seed_var,
            fg_color=tm.c("ACCENT"),
            text_color=tm.c("TEXT_PRIMARY"),
            font=BODY,
        )
        self._seed_cb.pack(fill="x", pady=(PAD_MD, 0))

    def _on_slider_change(self, value):
        v = int(value)
        if v % 2 != 0:
            v += 1
        self._max_teams_label.configure(text=str(v))

    def _create(self):
        toast = ToastManager()
        name = self._name_entry.get().strip()
        game = self._game_entry.get().strip()
        t_type = self._type_menu.get()
        max_teams = int(self._max_teams_var.get())
        seed_demo = self._seed_var.get()

        if not name:
            toast.show("Tournament name is required", "error")
            return

        if self._on_create:
            self._on_create(name, game, t_type, max_teams, seed_demo)
        self.close()


class NotificationModal(Modal):

    def __init__(self, parent, notifications):
        super().__init__(parent, title="Notifications", width=500, height=600)
        self._cancel_btn.pack_forget()
        self.set_action_text("Clear All")
        self.set_action_command(self._clear_notifications)
        self.parent = parent
        self.notifications = notifications
        self._render_notifications()

    def _render_notifications(self):
        for widget in self.body.winfo_children():
            widget.destroy()

        if not self.notifications:
            empty_lbl = ctk.CTkLabel(
                self.body, text="No notifications",
                font=BODY, text_color=ThemeManager().c("TEXT_MUTED")
            )
            empty_lbl.pack(pady=40)
            return

        tm = ThemeManager()
        for event in reversed(self.notifications):
            card = ctk.CTkFrame(self.body, fg_color=tm.c("BG_SURFACE"),
                                   corner_radius=8, border_width=1,
                                   border_color=tm.c("BORDER"))
            card.pack(fill="x", pady=4, padx=4)

            color_val = tm.c(event.color)
            accent = ctk.CTkFrame(card, width=4, fg_color=color_val, corner_radius=0)
            accent.pack(side="left", fill="y")

            content = ctk.CTkFrame(card, fg_color="transparent")
            content.pack(side="left", fill="both", expand=True, padx=PAD_MD, pady=PAD_SM)

            time_lbl = ctk.CTkLabel(content, text=event.timestamp, font=SMALL,
                                     text_color=tm.c("TEXT_MUTED"))
            time_lbl.pack(anchor="w")

            desc_lbl = ctk.CTkLabel(content, text=event.description, font=BODY,
                                     text_color=tm.c("TEXT_PRIMARY"), wraplength=400,
                                     justify="left")
            desc_lbl.pack(anchor="w", pady=(2, 0))

    def _clear_notifications(self):
        self.parent.service.notification_sub.notifications.clear()
        self.parent.service.notification_sub.unread_count = 0
        self.parent.topbar.update_notification_badge(0)
        self.notifications = []
        self._render_notifications()
