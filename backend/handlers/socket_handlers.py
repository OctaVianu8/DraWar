from flask_socketio import emit, join_room, leave_room

from backend.services.game_manager import game_manager
from backend.state.game_store import store

def register_handlers(socketio):
    game_manager.set_socketio(socketio)
    
    @socketio.on('connect')
    def handle_connect():
        emit('connected', {'message': 'Connected to DraWar server'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        from flask import request
        
        result = game_manager.disconnect_player(request.sid)
        if result:
            player, lobby = result
            
            if lobby:
                emit('player_left', {
                    'player_id': player.id,
                    'username': player.username,
                    'lobby': lobby.to_dict()
                }, room=lobby.id)
    
    @socketio.on('authenticate')
    def handle_authenticate(data):
        from flask import request
        
        username = data.get('username', '').strip()
        if not username:
            username = f"Player_{request.sid[:6]}"
        
        player = game_manager.authenticate_player(request.sid, username)
        
        emit('authenticated', {
            'player_id': player.id,
            'username': player.username
        })
    
    
    
    @socketio.on('leave_game')
    def handle_leave_game(data=None):
        handle_leave_lobby(data)

    
    @socketio.on('player_ready')
    def handle_player_ready(data=None):
        from flask import request
        
        player = store.get_player_by_socket(request.sid)
        if not player or not player.current_lobby_id:
            emit('error', {'code': 'NOT_IN_LOBBY', 'message': 'Not in a lobby'})
            return
        
        lobby = game_manager.set_player_ready(player.id)
        
        current_lobby = store.get_lobby(player.current_lobby_id)
        emit('player_ready_update', {
            'player_id': player.id,
            'username': player.username,
            'lobby': current_lobby.to_dict() if current_lobby else None
        }, room=player.current_lobby_id)
        
        if lobby:
            emit('game_starting', {'countdown': 3}, room=lobby.id)
            
            def start_after_countdown():
                import eventlet
                eventlet.sleep(3)
                word = game_manager.start_game_in_lobby(lobby.id)
                if word:
                    game = lobby.current_game
                    socketio.emit('round_start', {
                        'lobby_id': lobby.id,
                        'game_id': game.id if game else None,
                        'round_id': game.current_round.id if game and game.current_round else None,
                        'round_number': (game.rounds_played + 1) if game else 1,
                        'word': word,
                        'duration': game.current_round.duration if game and game.current_round else 60
                    }, room=lobby.id)
            
            socketio.start_background_task(start_after_countdown)
    
    @socketio.on('play_again')
    def handle_play_again(data=None):
        from flask import request
        
        player = store.get_player_by_socket(request.sid)
        if not player or not player.current_lobby_id:
            emit('error', {'code': 'NOT_IN_LOBBY', 'message': 'Not in a lobby'})
            return
        
        lobby, should_start = game_manager.mark_ready_for_next(player.id)
        
        if lobby is None:
            emit('error', {'code': 'LOBBY_NOT_FOUND', 'message': 'Lobby not found'})
            return
        
        if should_start:
            emit('game_starting', {'countdown': 3}, room=lobby.id)
            
            def start_after_countdown():
                import eventlet
                eventlet.sleep(3)
                word = game_manager.start_game_in_lobby(lobby.id)
                if word:
                    game = lobby.current_game
                    socketio.emit('round_start', {
                        'lobby_id': lobby.id,
                        'game_id': game.id if game else None,
                        'round_id': game.current_round.id if game and game.current_round else None,
                        'round_number': (game.rounds_played + 1) if game else 1,
                        'word': word,
                        'duration': game.current_round.duration if game and game.current_round else 60
                    }, room=lobby.id)
            
            socketio.start_background_task(start_after_countdown)
    
    @socketio.on('get_available_lobbies')
    def handle_get_available_lobbies(data=None):
        lobbies = game_manager.get_available_lobbies()
        emit('available_lobbies', {'lobbies': lobbies})
    
    @socketio.on('get_available_games')
    def handle_get_available_games(data=None):
        lobbies = game_manager.get_available_lobbies()
        emit('available_games', {'games': lobbies})
    
    # TODO: Add draw_update handler when image_processor and ai_service are implemented
    # TODO: Add submit_drawing handler when image_processor and ai_service are implemented
