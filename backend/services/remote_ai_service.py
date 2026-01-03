import json
from typing import List, Optional

import numpy as np
import requests
from requests.exceptions import RequestException

from backend.config import AI_SERVICE_URL
from backend.services.ai_service import AIServiceInterface, Prediction


class RemoteAIService(AIServiceInterface):
    def __init__(
        self,
        predict_url: Optional[str] = None,
        health_url: Optional[str] = None,
        timeout: float = 5.0,
        top_k: int = 5,
    ):
        self.predict_url = predict_url or AI_SERVICE_URL
        
        if health_url:
            self.health_url = health_url
        else:
            base_url = self.predict_url.rsplit('/predict', 1)[0]
            self.health_url = f"{base_url}/health"
        
        self.timeout = timeout
        self.top_k = top_k
    
    
