from flask import Flask, render_template
from flask_socketio import SocketIO
from flask_cors import CORS

from backend.config import DEBUG, PORT, SECRET_KEY
from backend.handlers.socket_handlers import register_handlers


def create_app():
    app = Flask(__name__, template_folder='../templates')
    app.config['SECRET_KEY'] = SECRET_KEY
    
    # Enable CORS for ngrok and cross-origin requests
    CORS(app, origins="*")
    
    return app


def create_socketio(app):
    socketio = SocketIO(
        app,
        cors_allowed_origins="*",
        async_mode='eventlet',
        logger=DEBUG,
        engineio_logger=DEBUG
    )
    
    # Register all event handlers
    register_handlers(socketio)
    
    return socketio


# Create app and socketio instances
app = create_app()
socketio = create_socketio(app)


# === HTTP Routes (for health checks and basic info) ===

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/health')
def health():
    from backend.state.game_store import store
    stats = store.get_stats()
    return {
        'status': 'healthy',
        'stats': stats
    }


@app.route('/api/games')
def list_games():
    from backend.services.game_manager import game_manager
    return {'games': game_manager.get_available_games()}


# === Main Entry Point ===

if __name__ == '__main__':
    print(f"""
    ╔═══════════════════════════════════════════╗
    ║           DraWar Backend Server           ║
    ╠═══════════════════════════════════════════╣
    ║  Running on: http://localhost:{PORT}      ║
    ║  Debug mode: {str(DEBUG).ljust(27)}       ║
    ║  WebSocket:  Socket.IO (eventlet)         ║
    ╚═══════════════════════════════════════════╝
    """)
    
    socketio.run(app, debug=DEBUG, port=PORT, host='0.0.0.0')
