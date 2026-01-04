from backend.server import app, socketio
from backend.config import PORT, DEBUG

if __name__ == "__main__":
    print(f"Starting DraWar from app.py on port {PORT}...")
    socketio.run(app, debug=DEBUG, port=PORT, host='0.0.0.0')
