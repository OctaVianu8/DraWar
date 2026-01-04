from typing import Optional, Tuple, List
from datetime import datetime
import eventlet

from backend.models.player import Player
from backend.models.game import Game, GameState
from backend.models.lobby import Lobby, LobbyState
from backend.state.game_store import store
from backend.services.word_generator import word_generator
from backend.services.image_processor import image_processor
from backend.services.ai_service import get_ai_service, Prediction
from backend.config import (
    AI_CONFIDENCE_THRESHOLD,
    MAX_DRAW_UPDATES_PER_SECOND,
)

class GameManager:
    def __init__(self, socketio=None):
        self.socketio = socketio
        self._round_timers: dict[str, eventlet.greenthread.GreenThread] = {}
        self._player_rate_limits: dict[str, datetime] = {}
    
    def set_socketio(self, socketio) -> None:
        self.socketio = socketio
    
    def authenticate_player(self, socket_id: str, username: str) -> Player:
        player = Player(username=username, socket_id=socket_id)
        store.add_player(player)
        return player
    
    def disconnect_player(self, socket_id: str) -> Optional[Tuple[Player, Optional[Lobby]]]:
        player = store.get_player_by_socket(socket_id)
        if player is None:
            return None
        
        affected_lobby = None
        if player.current_lobby_id:
            lobby = store.get_lobby(player.current_lobby_id)
            if lobby:
                affected_lobby = lobby
                if lobby.current_game and lobby.current_game.state == GameState.PLAYING:
                    self._handle_player_left_during_game(lobby)
                
                lobby.remove_player(player.id)
                
                if lobby.player_count == 0:
                    store.remove_lobby(lobby.id)
                    affected_lobby = None
        
        store.remove_player(player.id)
        return player, affected_lobby
    
    def _handle_player_left_during_game(self, lobby: Lobby) -> None:
        game = lobby.current_game
        if game and game.current_round and game.current_round.is_active:
            game.end_round(winner_id=None)
        
        if game:
            game.state = GameState.FINISHED
            self._cancel_round_timer(game.id)
        
        lobby.end_current_game()
    
    def create_lobby(self, player_id: str) -> Optional[Lobby]:
        player = store.get_player(player_id)
        if player is None:
            return None
        
        if player.current_lobby_id:
            self.leave_lobby(player_id)
        
        lobby = store.create_lobby()
        lobby.add_player(player)
        
        return lobby
    
    def join_lobby(self, player_id: str, lobby_id: str) -> Tuple[bool, str]:
        player = store.get_player(player_id)
        if player is None:
            return False, "Player not found"
        
        lobby = store.get_lobby(lobby_id)
        if lobby is None:
            return False, "Lobby not found"
        
        if lobby.is_full:
            return False, "Lobby is full"
        
        if lobby.state == LobbyState.IN_GAME:
            return False, "Game is in progress"
        
        if player.current_lobby_id:
            self.leave_lobby(player_id)
        
        if not lobby.add_player(player):
            return False, "Could not join lobby"
        
        return True, ""
    
    def leave_lobby(self, player_id: str) -> Optional[Lobby]:
        player = store.get_player(player_id)
        if player is None or player.current_lobby_id is None:
            return None
        
        lobby = store.get_lobby(player.current_lobby_id)
        if lobby is None:
            return None
        
        if lobby.current_game and lobby.current_game.state == GameState.PLAYING:
            self._handle_player_left_during_game(lobby)
        
        lobby.remove_player(player_id)
        
        if lobby.player_count == 0:
            store.remove_lobby(lobby.id)
            return None
        
        return lobby
    
    def set_player_ready(self, player_id: str) -> Optional[Lobby]:
        player = store.get_player(player_id)
        if player is None or player.current_lobby_id is None:
            return None
        
        lobby = store.get_lobby(player.current_lobby_id)
        if lobby is None:
            return None
        
        player.is_ready = True
        
        if lobby.all_players_ready and lobby.state in (LobbyState.WAITING, LobbyState.GAME_OVER):
            return lobby
        
        return None
    
    def mark_ready_for_next(self, player_id: str) -> Tuple[Optional[Lobby], bool]:
        player = store.get_player(player_id)
        if player is None or player.current_lobby_id is None:
            return None, False
        
        lobby = store.get_lobby(player.current_lobby_id)
        if lobby is None:
            return None, False
        
        if lobby.state != LobbyState.GAME_OVER:
            return lobby, False
        
        lobby.mark_ready_for_next(player_id)
        
        if self.socketio:
            self.socketio.emit('player_ready_for_next', {
                'lobby_id': lobby.id,
                'player_id': player_id,
                'username': player.username,
                'lobby': lobby.to_dict()
            }, room=lobby.id)
        
        if lobby.all_ready_for_next:
            return lobby, True
        
        return lobby, False
    
    def start_game_in_lobby(self, lobby_id: str) -> Optional[str]:
        lobby = store.get_lobby(lobby_id)
        if lobby is None:
            return None
        game = lobby.start_new_game()
        store.add_game(game)
        game.state = GameState.STARTING
        word = word_generator.get_random_word()
        game.start_round(word)
        self._start_round_timer(game.id)
        return word
    
    def _start_round_timer(self, game_id: str) -> None:
        game = store.get_game(game_id)
        if game is None or game.current_round is None:
            return
        
        duration = game.current_round.duration
        
        def timer_callback():
            eventlet.sleep(duration)
            self._on_round_timeout(game_id)
        
        gt = eventlet.spawn(timer_callback)
        self._round_timers[game_id] = gt
    
    def _cancel_round_timer(self, game_id: str) -> None:
        gt = self._round_timers.pop(game_id, None)
        if gt:
            gt.kill()
    
    def _on_round_timeout(self, game_id: str) -> None:
        game = store.get_game(game_id)
        if game is None or game.current_round is None:
            return
        
        lobby = store.get_lobby(game.lobby_id)
        game.end_round(winner_id=None)
        if self.socketio and lobby:
            self.socketio.emit('round_end', {
                'lobby_id': lobby.id,
                'game_id': game_id,
                'winner_id': None,
                'word': game.round_history[-1].word if game.round_history else None,
                'scores': game.get_scores(),
                'timeout': True
            }, room=lobby.id)
        
        if game.state == GameState.FINISHED:
            self._end_game(game, lobby)
        else:
            self._start_next_round(game, lobby)
    
    def _start_next_round(self, game: Game, lobby: Lobby) -> None:
        if game is None or lobby is None:
            return
        
        used_words = {r.word for r in game.round_history}
        word = word_generator.get_random_word(exclude=used_words)
        
        game.start_round(word)
        self._start_round_timer(game.id)
        
        if self.socketio:
            self.socketio.emit('round_start', {
                'lobby_id': lobby.id,
                'game_id': game.id,
                'round_id': game.current_round.id,
                'round_number': game.rounds_played + 1,
                'word': word,
                'duration': game.current_round.duration
            }, room=lobby.id)
    
    def _end_game(self, game: Game, lobby: Lobby) -> None:
        winner = game.get_winner()
        if lobby:
            lobby.end_current_game()
        
        if self.socketio and lobby:
            self.socketio.emit('game_end', {
                'lobby_id': lobby.id,
                'game_id': game.id,
                'winner_id': winner.id if winner else None,
                'winner_username': winner.username if winner else None,
                'final_scores': game.get_scores(),
                'lobby': lobby.to_dict()
            }, room=lobby.id)
    
    def handle_draw_update(
        self, 
        player_id: str, 
        canvas_data: str
    ) -> Optional[Tuple[List[Prediction], bool]]:
        player = store.get_player(player_id)
        if player is None or player.current_lobby_id is None:
            return None
        
        lobby = store.get_lobby(player.current_lobby_id)
        if lobby is None or lobby.current_game is None:
            return None
        
        game = lobby.current_game
        current_round = game.current_round
        if game.state != GameState.PLAYING or current_round is None:
            return None
        
        target_word = current_round.word.lower()
        
        if not self._check_rate_limit(player_id):
            return None
        
        image_array = image_processor.process_canvas_data(canvas_data)
        if image_array is None:
            return None
        
        current_round.update_drawing(player_id, canvas_data)
        
        ai_service = get_ai_service()
        predictions = ai_service.predict(image_array)
        
        would_be_correct = any(
            p.label.lower() == target_word and p.confidence >= AI_CONFIDENCE_THRESHOLD
            for p in predictions
        )
        
        return predictions, would_be_correct
    
    def submit_drawing(
        self, 
        player_id: str, 
        canvas_data: str
    ) -> Optional[Tuple[List[Prediction], bool]]:
        player = store.get_player(player_id)
        if player is None or player.current_lobby_id is None:
            return None
        
        lobby = store.get_lobby(player.current_lobby_id)
        if lobby is None or lobby.current_game is None:
            return None
        
        game = lobby.current_game
        current_round = game.current_round
        if game.state != GameState.PLAYING or current_round is None:
            return None
        
        target_word = current_round.word.lower()
        
        image_array = image_processor.process_canvas_data(canvas_data)
        if image_array is None:
            return None
        
        ai_service = get_ai_service()
        predictions = ai_service.predict(image_array)
        
        is_correct = any(
            p.label.lower() == target_word and p.confidence >= AI_CONFIDENCE_THRESHOLD
            for p in predictions
        )
        
        if is_correct:
            self._handle_correct_prediction(game, lobby, player_id)
        
        return predictions, is_correct
    
    def _check_rate_limit(self, player_id: str) -> bool:
        now = datetime.now()
        last_update = self._player_rate_limits.get(player_id)
        
        if last_update:
            elapsed = (now - last_update).total_seconds()
            min_interval = 1.0 / MAX_DRAW_UPDATES_PER_SECOND
            if elapsed < min_interval:
                return False
        
        self._player_rate_limits[player_id] = now
        return True
    
    def _handle_correct_prediction(self, game: Game, lobby: Lobby, winner_id: str) -> None:
        self._cancel_round_timer(game.id)
        
        word = game.current_round.word
        game.end_round(winner_id=winner_id)
        
        winner = game.get_player(winner_id)
        
        if self.socketio:
            self.socketio.emit('round_end', {
                'lobby_id': lobby.id,
                'game_id': game.id,
                'winner_id': winner_id,
                'winner_username': winner.username if winner else None,
                'word': word,
                'scores': game.get_scores(),
                'timeout': False
            }, room=lobby.id)
        
        if game.state == GameState.FINISHED:
            self._end_game(game, lobby)
        else:
            def delayed_next_round():
                eventlet.sleep(3.0)
                self._start_next_round(game, lobby)
            eventlet.spawn(delayed_next_round)
    
    def get_available_lobbies(self) -> List[dict]:
        return [lobby.to_dict() for lobby in store.get_available_lobbies()]
    
    def get_lobby_state(self, lobby_id: str) -> Optional[dict]:
        lobby = store.get_lobby(lobby_id)
        if lobby is None:
            return None
        return lobby.to_dict()

game_manager = GameManager()
