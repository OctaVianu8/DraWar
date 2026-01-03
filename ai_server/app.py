import os
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
    ║   :)    DraWar AI Inference Server   :)   ║
    ╠═══════════════════════════════════════════╣
    ║  Running on: http://localhost:5001        ║
    ║  Docs:       http://localhost:5001/docs   ║
    ╚═══════════════════════════════════════════╝
    """)
    
    uvicorn.run(app, host="0.0.0.0", port=5001)
