import uuid
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Player:
    username: str
    socket_id: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    score: int = 0
    is_ready: bool = False
    current_lobby_id: Optional[str] = None
    current_game_id: Optional[str] = None  
    
    def reset_for_new_game(self) -> None:
        self.score = 0
        self.is_ready = False
    
    def add_score(self, points: int) -> None:
        self.score += points
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "score": self.score,
            "is_ready": self.is_ready,
        }
    
    def __repr__(self) -> str:
        return f"Player(id={self.id[:8]}, username={self.username}, score={self.score})"
