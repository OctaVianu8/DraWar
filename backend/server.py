from flask import Flask, render_template
from flask_socketio import SocketIO
from flask_cors import CORS

from backend.config import DEBUG, PORT, SECRET_KEY
from backend.handlers.socket_handlers import register_handlers


def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config['SECRET_KEY'] = SECRET_KEY
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
    
    register_handlers(socketio)
    
    return socketio

app = create_app()
socketio = create_socketio(app)

from backend.services.ai_service import set_ai_service
from backend.services.remote_ai_service import RemoteAIService
set_ai_service(RemoteAIService())
print("[AI] Using RemoteAIService -> http://localhost:5001/predict")

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
