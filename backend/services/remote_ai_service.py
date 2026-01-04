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
        timeout: float = 15.0,
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
    
    def predict(self, image: np.ndarray) -> List[Prediction]:
        
        if image.shape != (28, 28):
            raise ValueError(f"Expected shape (28, 28) and got {image.shape}")
        
        if image.dtype != np.float32:
            image = image.astype(np.float32)
        
        payload = {
            "shape": [28, 28],
            "data": image.flatten().tolist(),
            "top_k": self.top_k,
        }
        
        try:
            response = requests.post(
                self.predict_url,
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            
        except RequestException as e:
            raise RuntimeError(f"AI service failed: {e}") from e
        
        try:
            data = response.json()
            predictions = []
            
            for pred in data.get("predictions", []):
                predictions.append(Prediction(
                    label=pred["label"],
                    confidence=pred["confidence"],
                ))
            
            return predictions
            
        except (json.JSONDecodeError, KeyError) as e:
            raise RuntimeError(f"Failed to parse: {e}") from e
    
    def is_available(self) -> bool:
        try:
            response = requests.get(
                self.health_url,
                timeout=self.timeout,
            )
            response.raise_for_status()
            
            data = response.json()
            return data.get("status") == "ok"
            
        except RequestException:
            return False
        except (json.JSONDecodeError, KeyError):
            return False
