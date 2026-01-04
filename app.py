# Eventlet monkey patching MUST be at the very top before any other imports
import eventlet
eventlet.monkey_patch()

from backend.server import app, socketio
from backend.config import PORT, DEBUG, AI_SERVICE_URL


if __name__ == "__main__":
    print(f"""
    ╔═══════════════════════════════════════════╗
    ║           DraWar Game Server              ║
    ╠═══════════════════════════════════════════╣
    ║  Running on: http://localhost:{PORT}         ║
    ║  AI Service: Remote (HuggingFace)         ║
    ║  Debug mode: {str(DEBUG).ljust(27)} ║
    ╚═══════════════════════════════════════════╝
    """)
    print(f"[AI] Using: {AI_SERVICE_URL}")
    
    socketio.run(app, debug=DEBUG, port=PORT, host='0.0.0.0')