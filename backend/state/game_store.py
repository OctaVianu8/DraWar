"""
Game Store
In-memory storage for game state. Single source of truth.
"""

from typing import Optional, Dict
from backend.models.player import Player
from backend.models.game import Game


class GameStore:
    """
    In-memory storage for all game state.
    This is the single source of truth for the application.
    
    In production, this could be replaced with Redis or another
    distributed cache for scalability.
    """
    
    _instance = None
    
    def __new__(cls):
        # Singleton pattern
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.games: Dict[str, Game] = {}
        self.players: Dict[str, Player] = {}
        self.socket_to_player: Dict[str, str] = {}  # socket_id -> player_id
        self._initialized = True
    
    # === Player Management ===
    
    def add_player(self, player: Player) -> None:
        self.players[player.id] = player
        self.socket_to_player[player.socket_id] = player.id
    
    def get_player(self, player_id: str) -> Optional[Player]:
        return self.players.get(player_id)
    
    def get_player_by_socket(self, socket_id: str) -> Optional[Player]:
        player_id = self.socket_to_player.get(socket_id)
        if player_id:
            return self.players.get(player_id)
        return None
    
    def remove_player(self, player_id: str) -> Optional[Player]:
        player = self.players.pop(player_id, None)
        if player:
            self.socket_to_player.pop(player.socket_id, None)
            # Also remove from any game they're in
            if player.current_game_id:
                game = self.get_game(player.current_game_id)
                if game:
                    game.remove_player(player_id)
        return player
    
    def remove_player_by_socket(self, socket_id: str) -> Optional[Player]:
        player_id = self.socket_to_player.get(socket_id)
        if player_id:
            return self.remove_player(player_id)
        return None
    
    # === Game Management ===
    
    def create_game(self) -> Game:
        game = Game()
        self.games[game.id] = game
        return game
    
    def get_game(self, game_id: str) -> Optional[Game]:
        return self.games.get(game_id)
    
    def remove_game(self, game_id: str) -> Optional[Game]:
        return self.games.pop(game_id, None)
    
    def get_available_games(self) -> list[Game]:
        from backend.models.game import GameState
        return [
            g for g in self.games.values()
            if g.state == GameState.LOBBY and not g.is_full
        ]
    
    # === Utility ===
    
    def clear(self) -> None: # For testing
        self.games.clear()
        self.players.clear()
        self.socket_to_player.clear()
    
    def get_stats(self) -> dict:
        return {
            "total_players": len(self.players),
            "total_games": len(self.games),
            "active_connections": len(self.socket_to_player),
        }

store = GameStore()
