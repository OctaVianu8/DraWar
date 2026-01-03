import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from ..config import ROUND_DURATION_SECONDS

@dataclass
class Round:
    game_id: str
    word: str
    duration: int = ROUND_DURATION_SECONDS
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    winner_id: Optional[str] = None
    player_drawings: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_active(self) -> bool:
        return self.end_time is None
    
    @property
    def time_remaining(self) -> float:
        if not self.is_active:
            return 0
        elapsed = (datetime.now() - self.start_time).total_seconds()
        return max(0, self.duration - elapsed)
    
    def update_drawing(self, player_id: str, canvas_data: Any) -> None:
        self.player_drawings[player_id] = canvas_data
    
    def set_winner(self, player_id: str) -> None:
        self.winner_id = player_id
        self.end_time = datetime.now()
    
    def end_without_winner(self) -> None:
        self.end_time = datetime.now()
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "game_id": self.game_id,
            "word": self.word,
            "duration": self.duration,
            "time_remaining": self.time_remaining,
            "is_active": self.is_active,
            "winner_id": self.winner_id,
        }
    
    def __repr__(self) -> str:
        status = "active" if self.is_active else "ended"
        return f"Round(id={self.id[:8]}, word={self.word}, status={status})"
