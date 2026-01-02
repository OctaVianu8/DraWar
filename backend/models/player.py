import uuid
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Player:
    """
    id: Unique identifier for the player
    username: Display name of the player
    socket_id: Socket.IO session ID for this player's connection
    score: Total score accumulated across rounds
    is_ready: Whether the player is ready to start the game
    current_game_id: ID of the game the player is currently in (if any)
    """
    username: str
    socket_id: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    score: int = 0
    is_ready: bool = False
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
