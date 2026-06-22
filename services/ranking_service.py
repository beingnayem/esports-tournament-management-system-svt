from typing import List, Dict
from patterns.strategy import RankingContext


class RankingService:

    def __init__(self):
        self.context = RankingContext("Points")

    def get_rankings(self, teams: list, matches: list,
                     strategy_name: str = None) -> List[dict]:
        if strategy_name:
            self.context.set_strategy(strategy_name)
        return self.context.get_rankings(teams, matches)

    def set_strategy(self, name: str):
        self.context.set_strategy(name)

    @property
    def current_strategy(self) -> str:
        return self.context.strategy.name

    @staticmethod
    def available_strategies() -> List[str]:
        return RankingContext.available_strategies()

    def get_trend(self, team, recent_matches: list) -> str:
        from models.match import MatchResult
        team_matches = [
            m for m in recent_matches
            if m.is_completed and (m.team1_id == team.id or m.team2_id == team.id)
        ]
        last3 = team_matches[-3:] if len(team_matches) >= 3 else team_matches

        if not last3:
            return "—"

        wins = 0
        losses = 0
        for m in last3:
            if m.result == MatchResult.TEAM1_WIN and m.team1_id == team.id:
                wins += 1
            elif m.result == MatchResult.TEAM2_WIN and m.team2_id == team.id:
                wins += 1
            elif m.result == MatchResult.DRAW:
                pass
            else:
                losses += 1

        if wins > losses:
            return "↑"
        elif losses > wins:
            return "↓"
        return "—"

    def get_team_stats_for_radar(self, team, all_teams: list,
                                 matches: list) -> Dict[str, float]:
        max_wins = max((t.wins for t in all_teams), default=1) or 1
        max_elo = max((t.elo for t in all_teams), default=1) or 1
        max_points = max((t.points for t in all_teams), default=1) or 1

        return {
            "Win Rate": team.win_rate,
            "Elo": (team.elo / max_elo) * 100,
            "Points": (team.points / max_points) * 100,
            "Wins": (team.wins / max_wins) * 100,
            "Consistency": 100 - ((team.losses / max(team.total_matches, 1)) * 100),
        }
