"""Tests de l'entraînement (C12) : smoke test de bout en bout sur un mini jeu
de données synthétique (2 classes, quelques images) pour rester rapide en CI —
le vrai entraînement sur TrashNet se fait séparément (voir ml/README.md et la
CI modèle qui télécharge le dataset complet)."""

import json

import pytest
from PIL import Image

from ml.scripts.train import train

pytestmark = pytest.mark.slow  # télécharge les poids MobileNetV3 pré-entraînés (~10 Mo) au premier lancement


def _make_split(base_dir, split_name: str, classes: dict[str, int]) -> None:
    for class_name, count in classes.items():
        class_dir = base_dir / split_name / class_name
        class_dir.mkdir(parents=True, exist_ok=True)
        for i in range(count):
            img = Image.new("RGB", (64, 64), color=(i * 10 % 255, 50, 100))
            img.save(class_dir / f"{class_name}_{i}.jpg")


@pytest.fixture
def tiny_dataset(tmp_path):
    data_dir = tmp_path / "processed"
    classes = {"verre": 6, "carton": 6}
    _make_split(data_dir, "train", classes)
    _make_split(data_dir, "val", classes)
    return data_dir


def test_train_runs_end_to_end_and_produces_expected_artifacts(tiny_dataset, tmp_path):
    output_dir = tmp_path / "models"
    reports_dir = tmp_path / "reports"

    result = train(
        data_dir=tiny_dataset,
        output_dir=output_dir,
        reports_dir=reports_dir,
        epochs=1,
        batch_size=4,
        seed=1,
    )

    assert result["classes"] == ["carton", "verre"]  # ImageFolder trie par ordre alphabétique
    assert (output_dir / "waste_classifier.pt").exists()
    assert (output_dir / "waste_classifier.onnx").exists()
    assert (output_dir / "labels.json").exists()
    assert (reports_dir / "train_history.json").exists()

    with open(reports_dir / "train_history.json", encoding="utf-8") as f:
        history = json.load(f)

    assert len(history["epochs"]) == 1
    epoch_record = history["epochs"][0]
    assert set(epoch_record) >= {"train_loss", "train_accuracy", "val_loss", "val_accuracy"}
    assert 0.0 <= epoch_record["train_accuracy"] <= 1.0
