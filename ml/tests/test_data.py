"""Tests de la préparation des données (C12) : validation du jeu brut,
découpage stratifié, matérialisation. Utilise un mini jeu de données synthétique
généré à la volée pour rester rapide, indépendant du vrai dataset TrashNet."""

from pathlib import Path

import pytest
from PIL import Image

from ml.scripts.prepare_data import (
    MIN_IMAGES_PER_CLASS,
    materialize_split,
    run,
    split_dataset,
    validate_raw_dataset,
)


def _make_fake_dataset(root: Path, classes: dict[str, int], corrupt_per_class: int = 0) -> Path:
    raw_dir = root / "raw"
    for class_name, count in classes.items():
        class_dir = raw_dir / class_name
        class_dir.mkdir(parents=True, exist_ok=True)
        for i in range(count):
            img = Image.new("RGB", (16, 16), color=(i % 255, 0, 0))
            img.save(class_dir / f"{class_name}_{i}.jpg")
        for i in range(corrupt_per_class):
            (class_dir / f"{class_name}_corrupt_{i}.jpg").write_bytes(b"not-a-real-image")
    return raw_dir


def test_validate_raw_dataset_accepts_valid_images(tmp_path):
    raw_dir = _make_fake_dataset(tmp_path, {"verre": MIN_IMAGES_PER_CLASS, "carton": MIN_IMAGES_PER_CLASS})
    report = validate_raw_dataset(raw_dir)

    assert set(report.valid.keys()) == {"verre", "carton"}
    assert len(report.valid["verre"]) == MIN_IMAGES_PER_CLASS
    assert report.corrupt == {}


def test_validate_raw_dataset_flags_corrupt_files_without_dropping_the_class(tmp_path):
    raw_dir = _make_fake_dataset(tmp_path, {"verre": MIN_IMAGES_PER_CLASS + 5}, corrupt_per_class=3)
    report = validate_raw_dataset(raw_dir)

    assert len(report.valid["verre"]) == MIN_IMAGES_PER_CLASS + 5
    assert len(report.corrupt["verre"]) == 3


def test_validate_raw_dataset_rejects_underrepresented_class(tmp_path):
    raw_dir = _make_fake_dataset(tmp_path, {"verre": MIN_IMAGES_PER_CLASS - 1})
    with pytest.raises(ValueError, match="insuffisamment représentée"):
        validate_raw_dataset(raw_dir)


def test_validate_raw_dataset_missing_dir_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        validate_raw_dataset(tmp_path / "does-not-exist")


def test_split_dataset_is_stratified_and_covers_all_images(tmp_path):
    raw_dir = _make_fake_dataset(tmp_path, {"verre": 100, "carton": 40})
    report = validate_raw_dataset(raw_dir)
    split = split_dataset(report.valid, seed=1)

    for class_name, total in {"verre": 100, "carton": 40}.items():
        covered = sum(len(split[s][class_name]) for s in ("train", "val", "test"))
        assert covered == total
        # chaque classe doit être présente dans train (le split le plus gros)
        assert len(split["train"][class_name]) > 0


def test_split_dataset_rejects_ratios_not_summing_to_one():
    with pytest.raises(ValueError, match="sommer"):
        split_dataset({"verre": []}, ratios={"train": 0.5, "val": 0.4, "test": 0.2})


def test_split_dataset_is_deterministic_given_the_same_seed(tmp_path):
    raw_dir = _make_fake_dataset(tmp_path, {"verre": 50})
    report = validate_raw_dataset(raw_dir)

    split_a = split_dataset(report.valid, seed=7)
    split_b = split_dataset(report.valid, seed=7)

    assert [p.name for p in split_a["train"]["verre"]] == [p.name for p in split_b["train"]["verre"]]


def test_materialize_split_writes_files_to_expected_layout(tmp_path):
    raw_dir = _make_fake_dataset(tmp_path, {"verre": 30})
    report = validate_raw_dataset(raw_dir)
    split = split_dataset(report.valid, seed=1)

    processed_dir = tmp_path / "processed"
    materialize_split(split, processed_dir)

    for split_name in ("train", "val", "test"):
        class_dir = processed_dir / split_name / "verre"
        assert class_dir.exists()
        expected_count = len(split[split_name]["verre"])
        assert len(list(class_dir.iterdir())) == expected_count


def test_run_end_to_end_produces_a_summary_report(tmp_path):
    raw_dir = _make_fake_dataset(tmp_path, {"verre": 30, "carton": 25})
    processed_dir = tmp_path / "processed"
    reports_dir = tmp_path / "reports"

    summary = run(raw_dir, processed_dir, reports_dir, seed=3)

    assert summary["total_valid"] == 55
    assert (reports_dir / "data_summary.json").exists()
    assert set(summary["split_counts"].keys()) == {"train", "val", "test"}
