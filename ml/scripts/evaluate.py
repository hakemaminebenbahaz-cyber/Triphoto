"""Évaluation et validation du modèle (C12, C13) sur le jeu de test.

Produit ml/reports/evaluation_report.json (accuracy, precision/recall/f1 par
classe, matrice de confusion) et ml/reports/confusion_matrix.png — c'est ce
rapport que la chaîne de livraison continue (C13) attache à la pull request.

`validate_against_threshold` sert de porte de qualité pour la CI : en dessous
du seuil, le pipeline doit échouer plutôt que déployer un modèle dégradé.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # pas d'affichage interactif : nécessaire en CI
import matplotlib.pyplot as plt
import torch
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from torch.utils.data import DataLoader
from torchvision import datasets

from ml.scripts.train import build_model

DEFAULT_ACCURACY_THRESHOLD = 0.60


def load_trained_model(model_dir: Path, device) -> tuple[torch.nn.Module, list[str], "transforms"]:
    with open(model_dir / "labels.json", encoding="utf-8") as f:
        classes = json.load(f)

    model, transform = build_model(num_classes=len(classes))
    state_dict = torch.load(model_dir / "waste_classifier.pt", map_location=device)
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()

    return model, classes, transform


def collect_predictions(model, loader, device) -> tuple[list[int], list[int]]:
    all_preds: list[int] = []
    all_labels: list[int] = []

    with torch.no_grad():
        for images, labels in loader:
            images = images.to(device)
            outputs = model(images)
            preds = outputs.argmax(dim=1).cpu().tolist()
            all_preds.extend(preds)
            all_labels.extend(labels.tolist())

    return all_preds, all_labels


def build_report(y_true: list[int], y_pred: list[int], classes: list[str]) -> dict:
    accuracy = accuracy_score(y_true, y_pred)
    per_class = classification_report(y_true, y_pred, target_names=classes, output_dict=True, zero_division=0)
    cm = confusion_matrix(y_true, y_pred).tolist()

    return {
        "accuracy": round(accuracy, 4),
        "classes": classes,
        "per_class": per_class,
        "confusion_matrix": cm,
    }


def plot_confusion_matrix(cm: list[list[int]], classes: list[str], output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(len(classes)))
    ax.set_yticks(range(len(classes)))
    ax.set_xticklabels(classes, rotation=45, ha="right")
    ax.set_yticklabels(classes)
    ax.set_xlabel("Prédit")
    ax.set_ylabel("Réel")
    ax.set_title("Matrice de confusion — TriPhoto")

    for i in range(len(classes)):
        for j in range(len(classes)):
            ax.text(j, i, cm[i][j], ha="center", va="center", color="black")

    fig.colorbar(im, ax=ax)
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)


def validate_against_threshold(accuracy: float, threshold: float = DEFAULT_ACCURACY_THRESHOLD) -> bool:
    """Porte de qualité utilisée par la CI (C13) : le pipeline échoue si le
    modèle nouvellement entraîné est moins bon que ce seuil minimal."""
    return accuracy >= threshold


def evaluate(data_dir: Path, model_dir: Path, reports_dir: Path, threshold: float = DEFAULT_ACCURACY_THRESHOLD) -> dict:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model, classes, transform = load_trained_model(model_dir, device)

    test_set = datasets.ImageFolder(data_dir / "test", transform=transform)
    test_loader = DataLoader(test_set, batch_size=32, shuffle=False, num_workers=0)

    y_pred, y_true = collect_predictions(model, test_loader, device)
    report = build_report(y_true, y_pred, classes)
    report["passes_quality_gate"] = validate_against_threshold(report["accuracy"], threshold)
    report["quality_threshold"] = threshold

    reports_dir.mkdir(parents=True, exist_ok=True)
    with open(reports_dir / "evaluation_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    plot_confusion_matrix(report["confusion_matrix"], classes, reports_dir / "confusion_matrix.png")

    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Évalue le modèle TriPhoto sur le jeu de test.")
    root = Path(__file__).resolve().parents[1]
    parser.add_argument("--data-dir", type=Path, default=root / "data" / "processed")
    parser.add_argument("--model-dir", type=Path, default=root / "models")
    parser.add_argument("--reports-dir", type=Path, default=root / "reports")
    parser.add_argument("--threshold", type=float, default=DEFAULT_ACCURACY_THRESHOLD)
    args = parser.parse_args()

    report = evaluate(args.data_dir, args.model_dir, args.reports_dir, threshold=args.threshold)
    print(json.dumps({"accuracy": report["accuracy"], "passes_quality_gate": report["passes_quality_gate"]}, indent=2))

    if not report["passes_quality_gate"]:
        raise SystemExit(
            f"Accuracy {report['accuracy']} en dessous du seuil de qualité {args.threshold} — échec volontaire pour la CI."
        )


if __name__ == "__main__":
    main()
