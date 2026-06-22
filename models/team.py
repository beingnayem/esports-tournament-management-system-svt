from dataclasses import dataclass, field
import uuid
from typing import List

from .player import Player

REGIONS = ["NA", "EU", "APAC", "SA", "CIS", "CN", "OCE", "MENA"]


@dataclass
class Team:

    name: str
    tag: str
    region: str = "NA"
    coach: str = ""
    founded_year: int = 2024
    players: List[Player] = field(default_factory=list)
    elo: float = 1000.0
    wins: int = 0
    losses: int = 0
    draws: int = 0
    points: int = 0
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def __post_init__(self):
        if not self.name or not self.name.strip():
            raise ValueError("Team name cannot be empty")
        if not self.tag or not self.tag.strip():
            raise ValueError("Team tag cannot be empty")
        if len(self.tag) > 6:
            raise ValueError(f"Team tag must be ≤6 characters, got '{self.tag}'")
        if self.region not in REGIONS:
            raise ValueError(f"Invalid region '{self.region}'. Must be one of {REGIONS}")

    @property
    def roster_size(self) -> int:
        return len(self.players)

    @property
    def win_rate(self) -> float:
        total = self.wins + self.losses + self.draws
        return (self.wins / total * 100) if total > 0 else 0.0

    @property
    def total_matches(self) -> int:
        return self.wins + self.losses + self.draws

    @property
    def goal_difference(self) -> int:
        return self.wins - self.losses

    def add_player(self, player: Player):
        if len(self.players) >= 10:
            raise ValueError("Team roster is full (max 10 players)")
        player.team_id = self.id
        self.players.append(player)

    def remove_player(self, player_id: str):
        self.players = [p for p in self.players if p.id != player_id]

    def record_win(self, points: int = 3):
        self.wins += 1
        self.points += points

    def record_loss(self, points: int = 0):
        self.losses += 1
        self.points += points

    def record_draw(self, points: int = 1):
        self.draws += 1
        self.points += points

    def update_elo(self, new_elo: float):
        self.elo = round(new_elo, 1)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "tag": self.tag,
            "region": self.region,
            "coach": self.coach,
            "founded_year": self.founded_year,
            "players": [p.to_dict() for p in self.players],
            "elo": self.elo,
            "wins": self.wins,
            "losses": self.losses,
            "draws": self.draws,
            "points": self.points,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Team":
        players = [Player.from_dict(p) for p in data.get("players", [])]
        t = cls(
            name=data["name"],
            tag=data["tag"],
            region=data.get("region", "NA"),
            coach=data.get("coach", ""),
            founded_year=data.get("founded_year", 2024),
            players=players,
            elo=data.get("elo", 1000.0),
            wins=data.get("wins", 0),
            losses=data.get("losses", 0),
            draws=data.get("draws", 0),
            points=data.get("points", 0),
        )
        t.id = data.get("id", t.id)
        return t

    def __str__(self):
        return f"[{self.tag}] {self.name}"
