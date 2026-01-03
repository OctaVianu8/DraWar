
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Set, Dict
from enum import Enum

from backend.models.player import Player
from backend.models.game import Game, GameState
from backend.config import MAX_PLAYERS_PER_GAME


class LobbyState(Enum):
    WAITING = "waiting"     
    READY = "ready"         
    IN_GAME = "in_game"     
    GAME_OVER = "game_over" 


@dataclass
class Lobby:

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    players: List[Player] = field(default_factory=list)
    current_game: Optional[Game] = None
    ready_for_next: Set[str] = field(default_factory=set)
    games_played: int = 0
    games_won: Dict[str, int] = field(default_factory=dict) 
    max_rounds: Optional[int] = None 
    state: LobbyState = LobbyState.WAITING
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def is_full(self) -> bool:
        return len(self.players) >= MAX_PLAYERS_PER_GAME
    
    @property
    def player_count(self) -> int:
        return len(self.players)
    
    @property
    def all_players_ready(self) -> bool:
        return len(self.players) >= 2 and all(p.is_ready for p in self.players)
    
    @property
    def all_ready_for_next(self) -> bool:
        return len(self.ready_for_next) >= len(self.players) and len(self.players) >= 2
    
    def get_rounds_for_game(self) -> int:
        if self.max_rounds is not None:
            return self.max_rounds
        return 5 + (self.player_count - 2) * 3
    
    def add_player(self, player: Player) -> bool:
        if self.is_full:
            return False
        if self.state == LobbyState.IN_GAME:
            return False
        
        player.current_lobby_id = self.id
        player.reset_for_new_game()
        self.players.append(player)
        if player.id not in self.games_won:
            self.games_won[player.id] = 0
        return True
    
    def remove_player(self, player_id: str) -> Optional[Player]:
        for i, player in enumerate(self.players):
            if player.id == player_id:
                removed = self.players.pop(i)
                removed.current_lobby_id = None
                self.ready_for_next.discard(player_id)
                return removed
        return None
    
    def get_player(self, player_id: str) -> Optional[Player]:
        for player in self.players:
            if player.id == player_id:
                return player
        return None
    
    def mark_ready_for_next(self, player_id: str) -> bool:
        if player_id not in {p.id for p in self.players}:
            return False
        self.ready_for_next.add(player_id)
        return True
    
    def is_player_ready_for_next(self, player_id: str) -> bool:
        return player_id in self.ready_for_next
    
    def record_game_win(self, winner_id: str) -> None:
        if winner_id in self.games_won:
            self.games_won[winner_id] += 1
        else:
            self.games_won[winner_id] = 1
    
    def start_new_game(self) -> Game:
        for player in self.players:
            player.score = 0
            player.is_ready = False
        self.ready_for_next.clear()
        self.current_game = Game(lobby_id=self.id, max_rounds=self.get_rounds_for_game())
        self.current_game.players = self.players.copy()
        self.state = LobbyState.IN_GAME
        
        return self.current_game
    
    def end_current_game(self) -> None:
        if self.current_game:
            winner = self.current_game.get_winner()
            if winner:
                self.record_game_win(winner.id)
        
        self.current_game = None
        self.games_played += 1
        self.state = LobbyState.GAME_OVER
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "state": self.state.value,
            "player_count": self.player_count,
            "max_players": MAX_PLAYERS_PER_GAME,
            "games_played": self.games_played,
            "max_rounds": self.max_rounds,
            "default_rounds": self.get_rounds_for_game(),
            "players": [
                {
                    "id": p.id,
                    "username": p.username,
                    "is_ready": p.is_ready,
                    "score": p.score,
                    "games_won": self.games_won.get(p.id, 0),
                    "ready_for_next": p.id in self.ready_for_next
                }
                for p in self.players
            ],
            "current_game": self.current_game.to_dict() if self.current_game else None,
        }
    
    def __repr__(self) -> str:
        return f"Lobby(id={self.id[:8]}, state={self.state.value}, players={self.player_count})"
