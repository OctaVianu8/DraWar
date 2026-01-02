# Game settings
ROUND_DURATION_SECONDS = 60
MAX_PLAYERS_PER_GAME = 2
MAX_ROUNDS_PER_GAME = 5
POINTS_PER_WIN = 1

# AI settings
AI_CONFIDENCE_THRESHOLD = 0.60  # 60% confidence to consider a correct guess
AI_SERVICE_URL = "http://localhost:5001/predict"  # Will be configured later

# Server settings
DEBUG = True
PORT = 5003
SECRET_KEY = "drawar-secret-key-change-in-production"

# Rate limiting for draw updates (max per second per player)
MAX_DRAW_UPDATES_PER_SECOND = 4
