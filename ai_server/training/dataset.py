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
    
    def _load_data(self):
        from itertools import islice
        
        np.random.seed(self.seed)
        
        print(f"Loading QuickDraw data for {len(self.categories)} categories...")
        
        for label_idx, category in enumerate(self.categories):
            print(f"  Loading '{category}'...")
            
            qd = QuickDrawData(recognized=True, max_drawings=self.samples_per_category)
            drawing_group = qd.get_drawing_group(category)
            
            category_images = []
            count = 0
            for drawing in drawing_group.drawings:
                if count >= self.samples_per_category:
                    break
                try:
                    img = drawing.get_image(stroke_width=2)
                    img = img.convert('L')
                    img = img.resize((28, 28))
                    img_array = np.array(img, dtype=np.float32) / 255.0
                    category_images.append(img_array)
                    count += 1
                except Exception as e:
                    continue
            
            n_train = int(len(category_images) * self.train_ratio)
            
            if self.split == "train":
                selected_images = category_images[:n_train]
            else:
                selected_images = category_images[n_train:]
            
            self.images.extend(selected_images)
            self.labels.extend([label_idx] * len(selected_images))
        
        print(f"Loaded {len(self.images)} samples for {self.split} split")
    
    def __len__(self) -> int:
        return len(self.images)
    
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        
        image = self.images[idx]
        label = self.labels[idx]
        
        image_tensor = torch.from_numpy(image).unsqueeze(0)
        
        return image_tensor, label
    
    def get_label_names(self) -> List[str]:
        return self.label_names


def create_dataloaders(
    categories: Optional[List[str]] = None,
    samples_per_category: int = 1000,
    batch_size: int = 64,
    num_workers: int = 0,
) -> Tuple[DataLoader, DataLoader, List[str]]:

    train_dataset = QuickDrawDataset(
        categories=categories,
        samples_per_category=samples_per_category,
        split="train",
    )
    
    val_dataset = QuickDrawDataset(
        categories=categories,
        samples_per_category=samples_per_category,
        split="val",
    )
    
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=True,
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=True,
    )
    
    return train_loader, val_loader, train_dataset.get_label_names()


def save_labels(label_names: List[str], save_path: str):
    with open(save_path, 'w') as f:
        json.dump(label_names, f, indent=2)
    print(f"Saved {len(label_names)} labels to {save_path}")


if __name__ == "__main__":
    train_loader, val_loader, labels = create_dataloaders(
        samples_per_category=100,
        batch_size=32,
    )
    
    print(f"\nTrain batches: {len(train_loader)}")
    print(f"Val batches: {len(val_loader)}")
    print(f"Labels: {labels}")
    
    images, batch_labels = next(iter(train_loader))
    print(f"\nBatch shape: {images.shape}")
    print(f"Labels shape: {batch_labels.shape}")

