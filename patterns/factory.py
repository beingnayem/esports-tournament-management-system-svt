from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class TournamentType(Enum):
    SINGLE_ELIMINATION = "Single Elimination"
    DOUBLE_ELIMINATION = "Double Elimination"
    ROUND_ROBIN = "Round Robin"
    SWISS = "Swiss"


@dataclass
class TournamentConfig:
    tournament_type: TournamentType
    name: str = "New Tournament"
    game: str = "CS2"
    max_teams: int = 8
    rounds: int = 0
    matches_per_round: int = 0
    has_losers_bracket: bool = False
    description: str = ""

    def __post_init__(self):
        if self.max_teams < 2:
            raise ValueError("Tournament must have at least 2 teams")
        self._compute_rounds()

    def _compute_rounds(self):
        n = self.max_teams
        if self.tournament_type == TournamentType.SINGLE_ELIMINATION:
            self.rounds = _log2_ceil(n)
            self.matches_per_round = n // 2
            self.has_losers_bracket = False
            self.description = (
                f"Single elimination bracket with {n} teams. "
                f"{self.rounds} rounds, one loss and you're out."
            )
        elif self.tournament_type == TournamentType.DOUBLE_ELIMINATION:
            self.rounds = _log2_ceil(n) * 2
            self.matches_per_round = n // 2
            self.has_losers_bracket = True
            self.description = (
                f"Double elimination bracket with {n} teams. "
                f"Teams must lose twice to be eliminated."
            )
        elif self.tournament_type == TournamentType.ROUND_ROBIN:
            self.rounds = n - 1
            self.matches_per_round = n // 2
            self.has_losers_bracket = False
            self.description = (
                f"Round robin with {n} teams. "
                f"Every team plays every other team once."
            )
        elif self.tournament_type == TournamentType.SWISS:
            self.rounds = _log2_ceil(n) + 1
            self.matches_per_round = n // 2
            self.has_losers_bracket = False
            self.description = (
                f"Swiss system with {n} teams over {self.rounds} rounds. "
                f"Teams are paired by similar records each round."
            )

    @property
    def total_matches(self) -> int:
        t = self.max_teams
        if self.tournament_type == TournamentType.SINGLE_ELIMINATION:
            return t - 1
        elif self.tournament_type == TournamentType.DOUBLE_ELIMINATION:
            return 2 * t - 2
        elif self.tournament_type == TournamentType.ROUND_ROBIN:
            return t * (t - 1) // 2
        elif self.tournament_type == TournamentType.SWISS:
            return self.rounds * (t // 2)
        return 0


def _log2_ceil(n: int) -> int:
    if n <= 1:
        return 0
    r = 0
    v = 1
    while v < n:
        v *= 2
        r += 1
    return r


class TournamentFactory:

    _type_map = {t.value: t for t in TournamentType}

    @classmethod
    def create(cls, type_name: str, **kwargs) -> TournamentConfig:
        t_type = cls._type_map.get(type_name)
        if t_type is None:
            raise ValueError(
                f"Unknown tournament type '{type_name}'. "
                f"Available: {list(cls._type_map.keys())}"
            )
        return TournamentConfig(tournament_type=t_type, **kwargs)

    @classmethod
    def available_types(cls) -> List[str]:
        return list(cls._type_map.keys())

    @classmethod
    def create_by_enum(cls, t_type: TournamentType, **kwargs) -> TournamentConfig:
        return TournamentConfig(tournament_type=t_type, **kwargs)
