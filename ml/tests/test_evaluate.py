"""Tests de l'évaluation et de la validation du modèle (C12, C13)."""

import json

import pytest
from PIL import Image

from ml.scripts.evaluate import (
    DEFAULT_ACCURACY_THRESHOLD,
    build_report,
    evaluate,
    validate_against_threshold,
)
from ml.scripts.train import train


def test_validate_against_threshold_passes_at_boundary():
    assert validate_against_threshold(0.60, threshold=0.60) is True


def test_validate_against_threshold_fails_below_boundary():
    assert validate_against_threshold(0.59, threshold=0.60) is False


def test_validate_against_threshold_uses_default_threshold():
    assert validate_against_threshold(DEFAULT_ACCURACY_THRESHOLD - 0.01) is False


def test_build_report_computes_accuracy_and_confusion_matrix_shape():
    y_true = [0, 0, 1, 1, 1]
    y_pred = [0, 1, 1, 1, 0]
    classes = ["carton", "verre"]

    report = build_report(y_true, y_pred, classes)

    assert report["accuracy"] == pytest.approx(3 / 5)
    assert report["classes"] == classes
    assert len(report["confusion_matrix"]) == 2
    assert len(report["confusion_matrix"][0]) == 2
    assert "carton" in report["per_class"]
    assert "verre" in report["per_class"]


def _make_split(base_dir, split_name: str, classes: dict[str, int]) -> None:
    for class_name, count in classes.items():
        class_dir = base_dir / split_name / class_name
        class_dir.mkdir(parents=True, exist_ok=True)
        for i in range(count):
            img = Image.new("RGB", (64, 64), color=(i * 10 % 255, 50, 100))
            img.save(class_dir / f"{class_name}_{i}.jpg")


@pytest.mark.slow
def test_evaluate_end_to_end_produces_report_and_confusion_matrix(tmp_path):
    data_dir = tmp_path / "processed"
    classes = {"verre": 6, "carton": 6}
    for split in ("train", "val", "test"):
        _make_split(data_dir, split, classes)

    model_dir = tmp_path / "models"
    reports_dir = tmp_path / "reports"

    train(data_dir=data_dir, output_dir=model_dir, reports_dir=reports_dir, epochs=1, batch_size=4, seed=1)
    report = evaluate(data_dir, model_dir, reports_dir, threshold=0.0)  # seuil à 0 : on teste juste que ça tourne

    assert (reports_dir / "evaluation_report.json").exists()
    assert (reports_dir / "confusion_matrix.png").exists()
    assert 0.0 <= report["accuracy"] <= 1.0
    assert report["passes_quality_gate"] is True  # seuil à 0 dans ce test

    with open(reports_dir / "evaluation_report.json", encoding="utf-8") as f:
        saved = json.load(f)
    assert saved["accuracy"] == report["accuracy"]
