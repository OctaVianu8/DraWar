import os

# Game settings
ROUND_DURATION_SECONDS = 30
MAX_PLAYERS_PER_GAME = 10
MAX_ROUNDS_PER_GAME = 5
POINTS_PER_WIN = 1

# AI settings
AI_CONFIDENCE_THRESHOLD = 0.80 
AI_SERVICE_URL = os.environ.get("AI_SERVICE_URL", "http://localhost:5001/predict") 

# Server settings
PRODUCTION = os.environ.get("PRODUCTION", "false").lower() == "true"
DEBUG = os.environ.get("DEBUG", "true").lower() == "true" if not PRODUCTION else False
PORT = int(os.environ.get("PORT", 5003))
SECRET_KEY = os.environ.get("SECRET_KEY", "drawar-secret-key-change-in-production")
MAX_DRAW_UPDATES_PER_SECOND = 4
