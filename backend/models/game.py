import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict

from backend.models.player import Player
from backend.models.round import Round
from backend.config import MAX_PLAYERS_PER_GAME, MAX_ROUNDS_PER_GAME


class GameState(Enum):
    LOBBY = "lobby"
    STARTING = "starting"
    PLAYING = "playing"
    ROUND_END = "round_end"
    FINISHED = "finished"


@dataclass
class Game:
    lobby_id: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    players: List[Player] = field(default_factory=list)
    current_round: Optional[Round] = None
    rounds_played: int = 0
    max_rounds: int = MAX_ROUNDS_PER_GAME
    state: GameState = GameState.LOBBY
    created_at: datetime = field(default_factory=datetime.now)
    round_history: List[Round] = field(default_factory=list)
    
    @property
    def is_full(self) -> bool:
        return len(self.players) >= MAX_PLAYERS_PER_GAME
    
    @property
    def all_players_ready(self) -> bool:
        return len(self.players) >= 2 and all(p.is_ready for p in self.players)
    
    @property
    def player_count(self) -> int:
        return len(self.players)
    
    def add_player(self, player: Player) -> bool:
        if self.is_full:
            return False
        if self.state != GameState.LOBBY:
            return False
        
        player.current_game_id = self.id
        player.reset_for_new_game()
        self.players.append(player)
        return True
    
    def remove_player(self, player_id: str) -> Optional[Player]:
        for i, player in enumerate(self.players):
            if player.id == player_id:
                removed = self.players.pop(i)
                removed.current_game_id = None
                return removed
        return None
    
    def get_player(self, player_id: str) -> Optional[Player]:
        for player in self.players:
            if player.id == player_id:
                return player
        return None
    
    def start_game(self) -> bool:
        if not self.all_players_ready:
            return False
        if self.state != GameState.LOBBY:
            return False
        
        self.state = GameState.STARTING
        return True
    
    def start_round(self, word: str) -> Round:
        self.current_round = Round(game_id=self.id, word=word)
        self.state = GameState.PLAYING
        return self.current_round
    
    def end_round(self, winner_id: Optional[str] = None) -> None:
        if self.current_round:
            if winner_id:
                self.current_round.set_winner(winner_id)
                winner = self.get_player(winner_id)
                if winner:
                    winner.add_score(1)
            else:
                self.current_round.end_without_winner()
            
            self.round_history.append(self.current_round)
            self.rounds_played += 1
        
        if self.rounds_played >= self.max_rounds:
            self.state = GameState.FINISHED
        else:
            self.state = GameState.ROUND_END
        
        self.current_round = None
    
    def get_scores(self) -> Dict[str, dict]:
        return {p.id: {'username': p.username, 'score': p.score} for p in self.players}
    
    def get_winner(self) -> Optional[Player]:
        if not self.players:
            return None
        return max(self.players, key=lambda p: p.score)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "state": self.state.value,
            "players": [p.to_dict() for p in self.players],
            "rounds_played": self.rounds_played,
            "max_rounds": self.max_rounds,
            "current_round": self.current_round.to_dict() if self.current_round else None,
        }
    
    def to_lobby_dict(self) -> dict:
        return {
            "id": self.id,
            "state": self.state.value,
            "player_count": self.player_count,
            "max_players": MAX_PLAYERS_PER_GAME,
            "players": [{"id": p.id, "username": p.username, "is_ready": p.is_ready} for p in self.players],
        }
    
    def __repr__(self) -> str:
        return f"Game(id={self.id[:8]}, state={self.state.value}, players={self.player_count})"
