from dataclasses import dataclass, field
import uuid

ROLES = ["Rifler", "AWPer", "IGL", "Support", "Entry"]


@dataclass
class Player:

    username: str
    role: str = "Rifler"
    age: int = 18
    team_id: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def __post_init__(self):
        if self.role not in ROLES:
            raise ValueError(f"Invalid role '{self.role}'. Must be one of {ROLES}")
        if self.age < 13 or self.age > 60:
            raise ValueError(f"Player age must be between 13 and 60, got {self.age}")
        if not self.username or not self.username.strip():
            raise ValueError("Player username cannot be empty")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role,
            "age": self.age,
            "team_id": self.team_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Player":
        p = cls(
            username=data["username"],
            role=data.get("role", "Rifler"),
            age=data.get("age", 18),
            team_id=data.get("team_id", ""),
        )
        p.id = data.get("id", p.id)
        return p

    def __str__(self):
        return f"{self.username} ({self.role})"
