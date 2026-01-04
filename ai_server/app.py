import sys
import json
from pathlib import Path
from typing import List, Optional

import numpy as np
import torch
import torch.nn as nn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).parent))

class PredictRequest(BaseModel):
    shape: List[int] = Field(..., description="Shape of the image array, e.g. [28, 28]")
    data: List[float] = Field(..., description="Flattened float array of pixel values [0,1]")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of top predictions to return")
    
    class Config:
        json_schema_extra = {
            "example": {
                "shape": [28, 28],
                "data": [0.0] * 784,
                "top_k": 5
            }
        }


class Prediction(BaseModel):
    label: str = Field(..., description="Category name")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score [0,1]")


class PredictResponse(BaseModel):
    predictions: List[Prediction]


class HealthResponse(BaseModel):
    status: str


class QuickDrawCNN(nn.Module):
    def __init__(self, num_classes: int):
        super().__init__()
        
        self.features = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),
            
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),
            
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),
        )
        
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(128 * 3 * 3, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(256, num_classes),
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.features(x)
        x = self.classifier(x)
        return x


class ModelManager:
    def __init__(self):
        self.model: Optional[nn.Module] = None
        self.labels: List[str] = []
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.is_loaded = False
    
    def load(self, model_dir: Path):
        model_path = model_dir / "model.pt"
        labels_path = model_dir / "labels.json"
        
        if not model_path.exists():
            print(f"Warning: Model file not found at {model_path}")
            print("Run training first: python training/train.py")
            return False
        
        if not labels_path.exists():
            print(f"Warning: Labels file not found at {labels_path}")
            return False
        
        with open(labels_path, 'r') as f:
            self.labels = json.load(f)
        
        checkpoint = torch.load(model_path, map_location=self.device, weights_only=False)
        num_classes = checkpoint.get('num_classes', len(self.labels))
        
        self.model = QuickDrawCNN(num_classes=num_classes)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model.to(self.device)
        self.model.eval()
        
        accuracy = checkpoint.get('accuracy', 'N/A')
        print(f"Loaded model with {num_classes} classes (accuracy: {accuracy}%)")
        print(f"Labels: {self.labels}")
        print(f"Device: {self.device}")
        
        self.is_loaded = True
        return True
    
    def predict(self, image: np.ndarray, top_k: int = 5) -> List[Prediction]:
        if not self.is_loaded:
            raise RuntimeError("Model not loaded")
        
        tensor = torch.from_numpy(image).float().unsqueeze(0).unsqueeze(0)
        tensor = tensor.to(self.device)
        
        with torch.no_grad():
            outputs = self.model(tensor)
            probabilities = torch.softmax(outputs, dim=1)
        
        top_probs, top_indices = torch.topk(probabilities[0], min(top_k, len(self.labels)))
        
        predictions = []
        for prob, idx in zip(top_probs.cpu().numpy(), top_indices.cpu().numpy()):
            predictions.append(Prediction(
                label=self.labels[idx],
                confidence=float(prob)
            ))
        
        return predictions


app = FastAPI(
    title="DraWar AI Service",
    description="AI inference server for drawing recognition",
    version="1.0.0",
)

model_manager = ModelManager()


@app.on_event("startup")
async def startup_event():
    model_dir = Path(__file__).parent / "model"
    success = model_manager.load(model_dir)
    
    if not success:
        print("\n" + "=" * 50)
        print("WARNING: Model not loaded!")
        print("The server will start but /predict will fail.")
        print("Run: python training/train.py")
        print("=" * 50 + "\n")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="ok")


@app.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest):
    if not model_manager.is_loaded:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Run training first: python training/train.py"
        )
    
    expected_size = request.shape[0] * request.shape[1]
    if len(request.data) != expected_size:
        raise HTTPException(
            status_code=400,
            detail=f"Data length {len(request.data)} doesn't match shape {request.shape}"
        )
    
    try:
        image = np.array(request.data, dtype=np.float32).reshape(request.shape)
        predictions = model_manager.predict(image, top_k=request.top_k)
        
        return PredictResponse(predictions=predictions)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    print("""
    ╔═══════════════════════════════════════════╗
    ║         DraWar AI Inference Server        ║
    ╠═══════════════════════════════════════════╣
    ║  Running on: https://eriko256-drawar-ai.hf.space ║
    ║  Docs:       /docs   ║
    ╚═══════════════════════════════════════════╝
    """)
    
    uvicorn.run(app, host="0.0.0.0", port=5001)
