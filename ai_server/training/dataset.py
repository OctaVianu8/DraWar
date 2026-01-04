import json
import numpy as np
from typing import List, Tuple, Optional
from pathlib import Path

import torch
from torch.utils.data import Dataset, DataLoader
from quickdraw import QuickDrawData

DEFAULT_CATEGORIES = [
  "cat",
  "dog",
  "house",
  "tree",
  "car",
  "fish",
  "flower",
  "sun",
  "star",
  "apple",
  "banana",
  "bird",
  "butterfly",
  "circle",
  "square",
  "airplane",
  "axe",
  "basketball",
  "bed",
  "bee",
  "bicycle",
  "camera",
  "cake",
  "dragon",
  "elephant",
  "face",
  "fork",
  "hamburger",
  "hat",
  "helicopter",
  "hourglass",
  "mushroom",
  "nose",
  "octagon",
  "pencil",
  "piano",
  "radio",
  "scissors",
  "shorts",
  "skateboard",
  "snowflake",
  "snowman",
  "spoon",
  "strawberry",
  "vase",
  "watermelon",
  "wheel",
  "zebra",
  "zigzag",
  "umbrella"
]


class QuickDrawDataset(Dataset):
    def __init__(
        self,
        categories: Optional[List[str]] = None,
        samples_per_category: int = 1000,
        split: str = "train",
        train_ratio: float = 0.8,
        seed: int = 42,
    ):
        self.categories = categories or DEFAULT_CATEGORIES
        self.samples_per_category = samples_per_category
        self.split = split
        self.train_ratio = train_ratio
        self.seed = seed
        
        self.images: List[np.ndarray] = []
        self.labels: List[int] = []
        self.label_names = self.categories.copy()
        
        self._load_data()
    
