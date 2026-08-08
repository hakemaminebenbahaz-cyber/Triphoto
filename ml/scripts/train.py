"""Entraînement du classifieur de déchets (C12, C13) par transfer learning :
backbone MobileNetV3-Small pré-entraîné (ImageNet) gelé, tête de classification
ré-entraînée sur les 6 classes du dataset TrashNet préparé par prepare_data.py.

Produit :
  - ml/models/waste_classifier.pt      (poids PyTorch, meilleure epoch sur val)
  - ml/models/waste_classifier.onnx    (export ONNX consommé par l'API)
  - ml/models/labels.json              (ordre des classes, index -> nom)
  - ml/reports/train_history.json      (loss/accuracy par epoch)
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import torch
from torch import nn
from torch.utils.data import DataLoader
from torchvision import datasets
from torchvision.models import MobileNet_V3_Small_Weights, mobilenet_v3_small


def build_model(num_classes: int) -> tuple[nn.Module, "torchvision.transforms.Compose"]:
    weights = MobileNet_V3_Small_Weights.DEFAULT
    model = mobilenet_v3_small(weights=weights)

    for param in model.features.parameters():
        param.requires_grad = False

    in_features = model.classifier[3].in_features
    model.classifier[3] = nn.Linear(in_features, num_classes)

    return model, weights.transforms()


def load_dataloaders(data_dir: Path, transform, batch_size: int) -> tuple[DataLoader, DataLoader, list[str]]:
    train_set = datasets.ImageFolder(data_dir / "train", transform=transform)
    val_set = datasets.ImageFolder(data_dir / "val", transform=transform)

    train_loader = DataLoader(train_set, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_set, batch_size=batch_size, shuffle=False, num_workers=0)

    return train_loader, val_loader, train_set.classes


def run_epoch(model, loader, criterion, optimizer, device, train: bool) -> tuple[float, float]:
    model.train(train)
    total_loss, correct, total = 0.0, 0, 0

    context = torch.enable_grad() if train else torch.no_grad()
    with context:
        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)

            if train:
                optimizer.zero_grad()

            outputs = model(images)
            loss = criterion(outputs, labels)

            if train:
                loss.backward()
                optimizer.step()

            total_loss += loss.item() * images.size(0)
            correct += (outputs.argmax(dim=1) == labels).sum().item()
            total += images.size(0)

    return total_loss / total, correct / total


def train(
    data_dir: Path,
    output_dir: Path,
    reports_dir: Path,
    epochs: int = 5,
    batch_size: int = 32,
    lr: float = 1e-3,
    seed: int = 42,
) -> dict:
    torch.manual_seed(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    output_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    probe = build_model(num_classes=1)  # juste pour récupérer les transforms par défaut
    _, transform = probe

    train_loader, val_loader, classes = load_dataloaders(data_dir, transform, batch_size)
    model, _ = build_model(num_classes=len(classes))
    model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.classifier.parameters(), lr=lr)

    history = []
    best_val_acc = 0.0
    best_state = None

    for epoch in range(1, epochs + 1):
        start = time.time()
        train_loss, train_acc = run_epoch(model, train_loader, criterion, optimizer, device, train=True)
        val_loss, val_acc = run_epoch(model, val_loader, criterion, optimizer, device, train=False)
        duration = time.time() - start

        history.append(
            {
                "epoch": epoch,
                "train_loss": round(train_loss, 4),
                "train_accuracy": round(train_acc, 4),
                "val_loss": round(val_loss, 4),
                "val_accuracy": round(val_acc, 4),
                "duration_seconds": round(duration, 1),
            }
        )
        print(
            f"epoch {epoch}/{epochs} - train_loss={train_loss:.4f} train_acc={train_acc:.4f} "
            f"val_loss={val_loss:.4f} val_acc={val_acc:.4f} ({duration:.1f}s)"
        )

        if val_acc >= best_val_acc:
            best_val_acc = val_acc
            best_state = {k: v.clone() for k, v in model.state_dict().items()}

    if best_state is not None:
        model.load_state_dict(best_state)

    torch.save(model.state_dict(), output_dir / "waste_classifier.pt")

    with open(output_dir / "labels.json", "w", encoding="utf-8") as f:
        json.dump(classes, f, ensure_ascii=False, indent=2)

    with open(reports_dir / "train_history.json", "w", encoding="utf-8") as f:
        json.dump({"classes": classes, "best_val_accuracy": round(best_val_acc, 4), "epochs": history}, f, indent=2)

    export_onnx(model, output_dir / "waste_classifier.onnx", device)

    return {"classes": classes, "best_val_accuracy": best_val_acc, "history": history}


def export_onnx(model: nn.Module, output_path: Path, device) -> None:
    model.eval()
    dummy_input = torch.randn(1, 3, 224, 224, device=device)
    torch.onnx.export(
        model,
        dummy_input,
        str(output_path),
        input_names=["image"],
        output_names=["logits"],
        dynamic_axes={"image": {0: "batch"}, "logits": {0: "batch"}},
        opset_version=18,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Entraîne le classifieur de déchets TriPhoto.")
    root = Path(__file__).resolve().parents[1]
    parser.add_argument("--data-dir", type=Path, default=root / "data" / "processed")
    parser.add_argument("--output-dir", type=Path, default=root / "models")
    parser.add_argument("--reports-dir", type=Path, default=root / "reports")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    train(
        args.data_dir,
        args.output_dir,
        args.reports_dir,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
