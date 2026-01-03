from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List
import numpy as np

@dataclass
class Prediction:
    label: str
    confidence: float
    
    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "confidence": round(self.confidence, 3)
        }

class AIServiceInterface(ABC):
    @abstractmethod
    def predict(self, image: np.ndarray) -> List[Prediction]:
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        pass


_ai_service: AIServiceInterface = None


def get_ai_service() -> AIServiceInterface:
    global _ai_service
    if _ai_service is None:
        raise RuntimeError("err")
    return _ai_service


def set_ai_service(service: AIServiceInterface) -> None:
    global _ai_service
    _ai_service = service
