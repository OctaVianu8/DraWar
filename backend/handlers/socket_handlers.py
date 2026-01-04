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
    
    @socketio.on('create_lobby')
    def handle_create_lobby(data=None):
        from flask import request
        
        player = store.get_player_by_socket(request.sid)
        if not player:
            emit('error', {'code': 'NOT_AUTHENTICATED', 'message': 'Please authenticate first'})
            return
        
        lobby = game_manager.create_lobby(player.id)
        if not lobby:
            emit('error', {'code': 'CREATE_FAILED', 'message': 'Could not create lobby'})
            return
        
        join_room(lobby.id)
        
        emit('lobby_created', {
            'lobby_id': lobby.id,
            'lobby': lobby.to_dict()
        })
    
    @socketio.on('create_game')
    def handle_create_game(data=None):
        handle_create_lobby(data)
    
    @socketio.on('join_lobby')
    def handle_join_lobby(data):
        from flask import request
        
        player = store.get_player_by_socket(request.sid)
        if not player:
            emit('error', {'code': 'NOT_AUTHENTICATED', 'message': 'Please authenticate first'})
            return
        
        lobby_id = data.get('lobby_id') or data.get('game_id')  # Support both
        if not lobby_id:
            emit('error', {'code': 'INVALID_DATA', 'message': 'Lobby ID required'})
            return
        
        success, error_msg = game_manager.join_lobby(player.id, lobby_id)
        
        if not success:
            emit('error', {'code': 'JOIN_FAILED', 'message': error_msg})
            return
        
        join_room(lobby_id)
        
        lobby = store.get_lobby(lobby_id)
        
        emit('joined_lobby', {
            'lobby_id': lobby_id,
            'lobby': lobby.to_dict() if lobby else None
        })
        
        emit('player_joined', {
            'player_id': player.id,
            'username': player.username,
            'lobby': lobby.to_dict() if lobby else None
        }, room=lobby_id)
    
    @socketio.on('join_game')
    def handle_join_game(data):
        handle_join_lobby(data)
    
    @socketio.on('leave_lobby')
    def handle_leave_lobby(data=None):
        from flask import request
        
        player = store.get_player_by_socket(request.sid)
        if not player or not player.current_lobby_id:
            return
        
        lobby_id = player.current_lobby_id
        lobby = game_manager.leave_lobby(player.id)
        
        leave_room(lobby_id)
        
        if lobby:
            emit('player_left', {
                'player_id': player.id,
                'username': player.username,
                'lobby': lobby.to_dict()
            }, room=lobby_id)
        
        emit('left_lobby', {'lobby_id': lobby_id})
    
    @socketio.on('leave_game')
    def handle_leave_game(data=None):
        handle_leave_lobby(data)
    
    @socketio.on('set_max_rounds')
    def handle_set_max_rounds(data):
        from flask import request
        
        player = store.get_player_by_socket(request.sid)
        if not player or not player.current_lobby_id:
            emit('error', {'code': 'NOT_IN_LOBBY', 'message': 'Not in a lobby'})
            return
        
        lobby = store.get_lobby(player.current_lobby_id)
        if not lobby:
            return
        
        max_rounds = data.get('max_rounds')
        if max_rounds is not None:
            max_rounds = int(max_rounds)
            if max_rounds < 1:
                max_rounds = None
            elif max_rounds > 20:
                max_rounds = 20
        
        lobby.max_rounds = max_rounds
        
        emit('lobby_settings_updated', {
            'lobby': lobby.to_dict()
        }, room=lobby.id)
    
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
    
    @socketio.on('get_lobby_state')
    def handle_get_lobby_state(data):
        lobby_id = data.get('lobby_id')
        if not lobby_id:
            emit('error', {'code': 'INVALID_DATA', 'message': 'Lobby ID required'})
            return
        
        state = game_manager.get_lobby_state(lobby_id)
        if not state:
            emit('error', {'code': 'LOBBY_NOT_FOUND', 'message': 'Lobby not found'})
            return
        
        emit('lobby_state', state)
    
    @socketio.on('get_game_state')
    def handle_get_game_state(data):
        handle_get_lobby_state(data)
