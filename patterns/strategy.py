from abc import ABC, abstractmethod
from typing import List, Dict, Tuple
import math


class RankingStrategy(ABC):

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def rank(self, teams: list, matches: list) -> List[dict]:
        pass


class PointsStrategy(RankingStrategy):

    @property
    def name(self) -> str:
        return "Points"

    def rank(self, teams: list, matches: list) -> List[dict]:
        ranked = []
        for team in teams:
            ranked.append({
                "team": team,
                "sort_value": team.points,
                "points": team.points,
                "wins": team.wins,
                "losses": team.losses,
                "draws": team.draws,
                "gd": team.goal_difference,
            })
        ranked.sort(key=lambda x: (x["sort_value"], x["gd"], x["wins"]), reverse=True)
        for i, entry in enumerate(ranked):
            entry["rank"] = i + 1
        return ranked


class WinRateStrategy(RankingStrategy):

    @property
    def name(self) -> str:
        return "Win Rate"

    def rank(self, teams: list, matches: list) -> List[dict]:
        ranked = []
        for team in teams:
            wr = team.win_rate
            ranked.append({
                "team": team,
                "sort_value": wr,
                "win_rate": round(wr, 1),
                "wins": team.wins,
                "losses": team.losses,
                "draws": team.draws,
                "total": team.total_matches,
            })
        ranked.sort(key=lambda x: (x["sort_value"], x["wins"]), reverse=True)
        for i, entry in enumerate(ranked):
            entry["rank"] = i + 1
        return ranked


class EloStrategy(RankingStrategy):

    K_FACTOR = 32

    @property
    def name(self) -> str:
        return "Elo"

    def rank(self, teams: list, matches: list) -> List[dict]:
        ranked = []
        for team in teams:
            ranked.append({
                "team": team,
                "sort_value": team.elo,
                "elo": round(team.elo, 1),
                "wins": team.wins,
                "losses": team.losses,
            })
        ranked.sort(key=lambda x: x["sort_value"], reverse=True)
        for i, entry in enumerate(ranked):
            entry["rank"] = i + 1
        return ranked

    @staticmethod
    def calculate_new_elo(winner_elo: float, loser_elo: float,
                          k: int = 32) -> Tuple[float, float]:
        expected_w = 1 / (1 + 10 ** ((loser_elo - winner_elo) / 400))
        expected_l = 1 - expected_w
        new_winner = winner_elo + k * (1 - expected_w)
        new_loser = loser_elo + k * (0 - expected_l)
        return round(new_winner, 1), round(new_loser, 1)


class HeadToHeadStrategy(RankingStrategy):

    @property
    def name(self) -> str:
        return "Head-to-Head"

    def rank(self, teams: list, matches: list) -> List[dict]:
        from models.match import MatchResult
        h2h: Dict[str, Dict[str, int]] = {}
        for team in teams:
            h2h[team.id] = {}

        for match in matches:
            if match.result == MatchResult.TEAM1_WIN:
                h2h.setdefault(match.team1_id, {})[match.team2_id] = \
                    h2h.get(match.team1_id, {}).get(match.team2_id, 0) + 1
            elif match.result == MatchResult.TEAM2_WIN:
                h2h.setdefault(match.team2_id, {})[match.team1_id] = \
                    h2h.get(match.team2_id, {}).get(match.team1_id, 0) + 1

        ranked = []
        for team in teams:
            h2h_wins = sum(h2h.get(team.id, {}).values())
            ranked.append({
                "team": team,
                "sort_value": h2h_wins,
                "h2h_wins": h2h_wins,
                "points": team.points,
                "wins": team.wins,
                "losses": team.losses,
                "draws": team.draws,
            })
        ranked.sort(key=lambda x: (x["sort_value"], x["points"], x["wins"]), reverse=True)
        for i, entry in enumerate(ranked):
            entry["rank"] = i + 1
        return ranked


class RankingContext:

    _strategies: Dict[str, RankingStrategy] = {
        "Points": PointsStrategy(),
        "Win Rate": WinRateStrategy(),
        "Elo": EloStrategy(),
        "Head-to-Head": HeadToHeadStrategy(),
    }

    def __init__(self, strategy_name: str = "Points"):
        self._strategy = self._strategies.get(strategy_name, PointsStrategy())

    @property
    def strategy(self) -> RankingStrategy:
        return self._strategy

    def set_strategy(self, name: str):
        if name in self._strategies:
            self._strategy = self._strategies[name]
        else:
            raise ValueError(
                f"Unknown strategy '{name}'. Available: {list(self._strategies.keys())}"
            )

    def get_rankings(self, teams: list, matches: list) -> List[dict]:
        return self._strategy.rank(teams, matches)

    @classmethod
    def available_strategies(cls) -> List[str]:
        return list(cls._strategies.keys())
