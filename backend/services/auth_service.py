import uuid
import secrets
from dataclasses import dataclass, field
from typing import Dict, Optional
from datetime import datetime, timedelta

@dataclass
class Session:
    token: str
    player_id: str
    username: str
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime = field(default_factory=lambda: datetime.now() + timedelta(hours=24))
    
    @property
    def is_expired(self) -> bool:
        return datetime.now() > self.expires_at


class AuthService:
    def __init__(self):
        self.sessions: Dict[str, Session] = {}
    
    def create_guest_session(self, username: str = None) -> Session:
        if not username:
            username = f"Guest_{uuid.uuid4().hex[:6].upper()}"
        
        token = secrets.token_urlsafe(32)
        player_id = str(uuid.uuid4())
        
        session = Session(
            token=token,
            player_id=player_id,
            username=username
        )
        
        self.sessions[token] = session
        return session
    
    def validate_token(self, token: str) -> Optional[Session]:
        session = self.sessions.get(token)
        
        if session is None:
            return None
        
        if session.is_expired:
            del self.sessions[token]
            return None
        
        return session
    
    def invalidate_session(self, token: str) -> bool:
        if token in self.sessions:
            del self.sessions[token]
            return True
        return False
    
    def cleanup_expired(self) -> int:
        expired = [
            token for token, session in self.sessions.items()
            if session.is_expired
        ]
        
        for token in expired:
            del self.sessions[token]
        
        return len(expired)


auth_service = AuthService()
