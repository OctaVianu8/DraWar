from typing import Optional, Dict
from backend.models.player import Player
from backend.models.game import Game
from backend.models.lobby import Lobby, LobbyState

class GameStore:
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.lobbies: Dict[str, Lobby] = {}
        self.games: Dict[str, Game] = {}
        self.players: Dict[str, Player] = {}
        self.socket_to_player: Dict[str, str] = {}
        self._initialized = True
    
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
            if player.current_lobby_id:
                lobby = self.get_lobby(player.current_lobby_id)
                if lobby:
                    lobby.remove_player(player_id)
        return player
    
    def remove_player_by_socket(self, socket_id: str) -> Optional[Player]:
        player_id = self.socket_to_player.get(socket_id)
        if player_id:
            return self.remove_player(player_id)
        return None
    
    def create_lobby(self) -> Lobby:
        lobby = Lobby()
        self.lobbies[lobby.id] = lobby
        return lobby
    
    def get_lobby(self, lobby_id: str) -> Optional[Lobby]:
        return self.lobbies.get(lobby_id)
    
    def remove_lobby(self, lobby_id: str) -> Optional[Lobby]:
        lobby = self.lobbies.pop(lobby_id, None)
        if lobby and lobby.current_game:
            self.games.pop(lobby.current_game.id, None)
        return lobby
    
    def get_available_lobbies(self) -> list[Lobby]:
        return [
            lobby for lobby in self.lobbies.values()
            if lobby.state in (LobbyState.WAITING, LobbyState.GAME_OVER) and not lobby.is_full
        ]
    
    def create_game(self) -> Game:
        game = Game()
        self.games[game.id] = game
        return game
    
    def get_game(self, game_id: str) -> Optional[Game]:
        return self.games.get(game_id)
    
    def add_game(self, game: Game) -> None:
        self.games[game.id] = game
    
    def remove_game(self, game_id: str) -> Optional[Game]:
        return self.games.pop(game_id, None)
    
    def get_available_games(self) -> list[Game]:
        from backend.models.game import GameState
        return [
            g for g in self.games.values()
            if g.state == GameState.LOBBY and not g.is_full
        ]
    
    def clear(self) -> None:
        self.lobbies.clear()
        self.games.clear()
        self.players.clear()
        self.socket_to_player.clear()
    
    def get_stats(self) -> dict:
        return {
            "total_players": len(self.players),
            "total_lobbies": len(self.lobbies),
            "total_games": len(self.games),
            "active_connections": len(self.socket_to_player),
        }

store = GameStore()
