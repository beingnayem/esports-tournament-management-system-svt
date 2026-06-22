from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid


class MatchResult(Enum):
    TEAM1_WIN = "team1_win"
    TEAM2_WIN = "team2_win"
    DRAW = "draw"
    PENDING = "pending"


class MatchStatus(Enum):
    SCHEDULED = "scheduled"
    CHECK_IN = "check_in"
    LIVE = "live"
    OVERTIME = "overtime"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DISPUTED = "disputed"


@dataclass
class Match:

    team1_id: str
    team2_id: str
    game: str = "CS2"
    score1: int = 0
    score2: int = 0
    status: MatchStatus = MatchStatus.SCHEDULED
    result: MatchResult = MatchResult.PENDING
    scheduled_time: str = ""
    round_number: int = 1
    bracket_position: int = 0
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def __post_init__(self):
        if not self.scheduled_time:
            self.scheduled_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        if self.team1_id == self.team2_id and self.team1_id != "":
            raise ValueError("A team cannot play against itself")

    @property
    def is_live(self) -> bool:
        return self.status in (MatchStatus.LIVE, MatchStatus.OVERTIME)

    @property
    def is_completed(self) -> bool:
        return self.status == MatchStatus.COMPLETED

    @property
    def is_scheduled(self) -> bool:
        return self.status == MatchStatus.SCHEDULED

    @property
    def score_display(self) -> str:
        return f"{self.score1}  —  {self.score2}"

    def determine_result(self) -> MatchResult:
        if self.score1 > self.score2:
            self.result = MatchResult.TEAM1_WIN
        elif self.score2 > self.score1:
            self.result = MatchResult.TEAM2_WIN
        else:
            self.result = MatchResult.DRAW
        return self.result

    @property
    def winner_id(self) -> str:
        if self.result == MatchResult.TEAM1_WIN:
            return self.team1_id
        elif self.result == MatchResult.TEAM2_WIN:
            return self.team2_id
        return ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "team1_id": self.team1_id,
            "team2_id": self.team2_id,
            "game": self.game,
            "score1": self.score1,
            "score2": self.score2,
            "status": self.status.value,
            "result": self.result.value,
            "scheduled_time": self.scheduled_time,
            "round_number": self.round_number,
            "bracket_position": self.bracket_position,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Match":
        m = cls(
            team1_id=data["team1_id"],
            team2_id=data["team2_id"],
            game=data.get("game", "CS2"),
            score1=data.get("score1", 0),
            score2=data.get("score2", 0),
            status=MatchStatus(data.get("status", "scheduled")),
            result=MatchResult(data.get("result", "pending")),
            scheduled_time=data.get("scheduled_time", ""),
            round_number=data.get("round_number", 1),
            bracket_position=data.get("bracket_position", 0),
        )
        m.id = data.get("id", m.id)
        return m

    def __str__(self):
        return f"Match {self.id}: {self.team1_id} vs {self.team2_id} [{self.status.value}]"
