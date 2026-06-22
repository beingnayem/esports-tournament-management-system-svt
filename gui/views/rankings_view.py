import customtkinter as ctk
from gui.theme import ThemeManager, H1, H2, H3, BODY, SMALL, PAD_SM, PAD_MD, PAD_LG, RADIUS
from gui.components.data_table import DataTable
from services.ranking_service import RankingService

try:
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import numpy as np
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


class RankingsView(ctk.CTkFrame):

    def __init__(self, parent, service=None):
        tm = ThemeManager()
        super().__init__(parent, fg_color=tm.c("BG_BASE"), corner_radius=0)

        self._tm = tm
        self._service = service
        self._ranking_service = RankingService()

        title = ctk.CTkLabel(
            self, text="Rankings", font=H1,
            text_color=tm.c("TEXT_PRIMARY"),
        )
        title.pack(fill="x", padx=PAD_LG, pady=(PAD_MD, PAD_SM))

        strategy_frame = ctk.CTkFrame(self, fg_color="transparent")
        strategy_frame.pack(fill="x", padx=PAD_LG, pady=(0, PAD_SM))

        strategies = RankingService.available_strategies()
        self._strategy_buttons = {}
        for strat in strategies:
            is_active = strat == "Points"
            btn = ctk.CTkButton(
                strategy_frame, text=strat, width=100, height=32,
                fg_color=tm.c("ACCENT") if is_active else tm.c("BG_ELEVATED"),
                hover_color=tm.c("ACCENT_HOVER") if is_active else tm.c("BG_HOVER"),
                text_color="#FFFFFF" if is_active else tm.c("TEXT_SECONDARY"),
                font=H3, corner_radius=6,
                command=lambda s=strat: self._set_strategy(s),
            )
            btn.pack(side="left", padx=2)
            self._strategy_buttons[strat] = btn

        columns = ["Rank", "Team", "Points", "W", "D", "L", "GD", "Elo", "Win%", "Trend"]
        col_widths = {"Rank": 50, "Team": 160, "Points": 60, "W": 40, "D": 40,
                      "L": 40, "GD": 50, "Elo": 70, "Win%": 60, "Trend": 50}

        self._table = DataTable(
            self, columns=columns, column_widths=col_widths,
        )
        self._table.pack(fill="both", expand=True, padx=PAD_LG, pady=(0, PAD_SM))

        self._chart_panel = ctk.CTkFrame(
            self, fg_color=tm.c("BG_SURFACE"),
            corner_radius=RADIUS, height=280,
        )
        self._chart_panel.pack(fill="x", padx=PAD_LG, pady=(0, PAD_LG))
        self._chart_panel.pack_propagate(False)

        chart_header = ctk.CTkLabel(
            self._chart_panel, text="Top 5 Teams Comparison", font=H3,
            text_color=tm.c("TEXT_PRIMARY"),
        )
        chart_header.pack(fill="x", padx=PAD_MD, pady=(PAD_MD, 0))

        self._chart_frame = ctk.CTkFrame(self._chart_panel, fg_color="transparent")
        self._chart_frame.pack(fill="both", expand=True, padx=PAD_SM, pady=PAD_SM)

    def refresh(self):
        if not self._service:
            return

        teams = self._service.get_all_teams()
        matches = self._service.get_all_matches()

        rankings = self._ranking_service.get_rankings(teams, matches)

        rows = []
        for entry in rankings:
            team = entry["team"]
            trend = self._ranking_service.get_trend(team, matches)
            wr = round(team.win_rate, 1)
            rows.append((
                entry["rank"], team.name, team.points,
                team.wins, team.draws, team.losses,
                team.goal_difference, round(team.elo, 0),
                f"{wr}%", trend,
            ))

        self._table.set_data(rows)

        try:
            children = list(self._table.tree.get_children())
            medal_colors = {0: "#FFD700", 1: "#C0C0C0", 2: "#CD7F32"}
            for idx, color in medal_colors.items():
                if idx < len(children):
                    self._table.tree.tag_configure(f"medal_{idx}",
                                                    background=self._tm.c("BG_SURFACE"))
        except Exception:
            pass

        self._refresh_radar(rankings[:5], teams, matches)

    def _set_strategy(self, strategy_name: str):
        self._ranking_service.set_strategy(strategy_name)
        tm = self._tm
        for name, btn in self._strategy_buttons.items():
            if name == strategy_name:
                btn.configure(fg_color=tm.c("ACCENT"),
                             hover_color=tm.c("ACCENT_HOVER"),
                             text_color="#FFFFFF")
            else:
                btn.configure(fg_color=tm.c("BG_ELEVATED"),
                             hover_color=tm.c("BG_HOVER"),
                             text_color=tm.c("TEXT_SECONDARY"))
        self.refresh()

    def _refresh_radar(self, top_rankings: list, all_teams: list, matches: list):
        if not HAS_MATPLOTLIB:
            return

        for widget in self._chart_frame.winfo_children():
            widget.destroy()

        if not top_rankings:
            return

        tm = self._tm
        categories = ["Win Rate", "Elo", "Points", "Wins", "Consistency"]
        N = len(categories)

        fig = Figure(figsize=(6, 2.2), dpi=100)
        fig.patch.set_facecolor(tm.c("BG_SURFACE"))
        ax = fig.add_subplot(111, polar=True)
        ax.set_facecolor(tm.c("BG_SURFACE"))

        angles = [n / float(N) * 2 * 3.14159 for n in range(N)]
        angles += angles[:1]

        colors = [tm.c("ACCENT"), tm.c("CYAN"), tm.c("GREEN"),
                  tm.c("AMBER"), tm.c("RED")]

        for i, entry in enumerate(top_rankings):
            team = entry["team"]
            stats = self._ranking_service.get_team_stats_for_radar(
                team, all_teams, matches
            )
            values = [stats.get(c, 0) for c in categories]
            values += values[:1]

            color = colors[i % len(colors)]
            ax.plot(angles, values, 'o-', linewidth=1.5, label=team.tag,
                    color=color, markersize=3)
            ax.fill(angles, values, alpha=0.1, color=color)

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, fontsize=7, color=tm.c("TEXT_SECONDARY"))
        ax.set_yticklabels([])
        ax.spines["polar"].set_color(tm.c("BORDER"))
        ax.grid(color=tm.c("BORDER"), linewidth=0.5)

        leg = ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1),
                        fontsize=7, framealpha=0.5)
        for text in leg.get_texts():
            text.set_color(tm.c("TEXT_SECONDARY"))

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, self._chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
