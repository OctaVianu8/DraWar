import subprocess
import sys
import time
import signal
import atexit
from pathlib import Path

from backend.server import app, socketio
from backend.config import PORT, DEBUG

ai_process = None


def start_ai_server():
    global ai_process
    
    ai_server_path = Path(__file__).parent / "ai_server" / "app.py"
    
    print("Starting AI server on port 5001...")
    ai_process = subprocess.Popen(
        [sys.executable, str(ai_server_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    time.sleep(2)
    
    if ai_process.poll() is not None:
        print("ERROR: AI server failed to start!")
        return False
    
    print("AI server started successfully")
    return True


def cleanup():
    global ai_process
    if ai_process is not None:
        print("\nShutting down AI server...")
        ai_process.terminate()
        try:
            ai_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            ai_process.kill()
        print("AI server stopped")


def signal_handler(signum, frame):
    cleanup()
    sys.exit(0)


if __name__ == "__main__":
    atexit.register(cleanup)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    if not start_ai_server():
        print("Failed to start AI server. Exiting.")
        sys.exit(1)
    
    print(f"\nStarting DraWar backend on port {PORT}...")
    try:
        socketio.run(app, debug=DEBUG, port=PORT, host='0.0.0.0')
    finally:
        cleanup()