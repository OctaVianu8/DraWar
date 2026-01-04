import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim.lr_scheduler import ReduceLROnPlateau
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent.parent))
from training.dataset import create_dataloaders, save_labels, DEFAULT_CATEGORIES


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


def train_epoch(
    model: nn.Module,
    train_loader,
    criterion: nn.Module,
    optimizer: optim.Optimizer,
    device: torch.device,
) -> float:
    model.train()
    total_loss = 0.0
    
    pbar = tqdm(train_loader, desc="Training", leave=False)
    for images, labels in pbar:
        images = images.to(device)
        labels = labels.to(device)
        
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        pbar.set_postfix({"loss": f"{loss.item():.4f}"})
    
    return total_loss / len(train_loader)


def validate(
    model: nn.Module,
    val_loader,
    criterion: nn.Module,
    device: torch.device,
) -> tuple:
    model.eval()
    total_loss = 0.0
    correct = 0
    total = 0
    
    with torch.no_grad():
        for images, labels in val_loader:
            images = images.to(device)
            labels = labels.to(device)
            
            outputs = model(images)
            loss = criterion(outputs, labels)
            total_loss += loss.item()
            
            _, predicted = torch.max(outputs, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
    
    accuracy = 100 * correct / total
    avg_loss = total_loss / len(val_loader)
    
    return avg_loss, accuracy


def main():
    parser = argparse.ArgumentParser(description="Train QuickDraw CNN")
    parser.add_argument("--epochs", type=int, default=15, help="Number of epochs")
    parser.add_argument("--batch-size", type=int, default=64, help="Batch size")
    parser.add_argument("--lr", type=float, default=0.001, help="Learning rate")
    parser.add_argument("--samples", type=int, default=2000, help="Samples per category")
    parser.add_argument("--categories", type=str, nargs="+", default=None, 
                        help="Categories to train on")
    args = parser.parse_args()
    
    script_dir = Path(__file__).parent
    model_dir = script_dir.parent / "model"
    model_dir.mkdir(exist_ok=True)
    
    model_path = model_dir / "model.pt"
    labels_path = model_dir / "labels.json"
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    print("\n" + "=" * 50)
    print("Loading dataset...")
    print("=" * 50)
    
    categories = args.categories or DEFAULT_CATEGORIES
    train_loader, val_loader, label_names = create_dataloaders(
        categories=categories,
        samples_per_category=args.samples,
        batch_size=args.batch_size,
    )
    
    num_classes = len(label_names)
    print(f"\nTraining on {num_classes} categories: {label_names}")
    
    model = QuickDrawCNN(num_classes=num_classes).to(device)
    print(f"\nModel parameters: {sum(p.numel() for p in model.parameters()):,}")
    
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=args.lr)
    scheduler = ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=2)
    
    print("\n" + "=" * 50)
    print("Starting training...")
    print("=" * 50)
    
    best_accuracy = 0.0
    
    for epoch in range(args.epochs):
        print(f"\nEpoch {epoch + 1}/{args.epochs}")
        
        train_loss = train_epoch(model, train_loader, criterion, optimizer, device)
        
        val_loss, val_accuracy = validate(model, val_loader, criterion, device)
        
        scheduler.step(val_loss)
        current_lr = optimizer.param_groups[0]['lr']
        
        print(f"  Train Loss: {train_loss:.4f}")
        print(f"  Val Loss: {val_loss:.4f} | Val Accuracy: {val_accuracy:.2f}%")
        print(f"  Learning Rate: {current_lr:.6f}")
        
        if val_accuracy > best_accuracy:
            best_accuracy = val_accuracy
            torch.save({
                'model_state_dict': model.state_dict(),
                'num_classes': num_classes,
                'accuracy': val_accuracy,
            }, model_path)
            print(f"  ✓ Saved best model (accuracy: {val_accuracy:.2f}%)")
    
    save_labels(label_names, labels_path)
    
    print("\n" + "=" * 50)
    print("Training complete!")
    print("=" * 50)
    print(f"Best validation accuracy: {best_accuracy:.2f}%")
    print(f"Model saved to: {model_path}")
    print(f"Labels saved to: {labels_path}")

if __name__ == "__main__":
    main()
