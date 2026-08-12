"""Préparation des données (C12) : validation du jeu brut, découpage stratifié
train/val/test, matérialisation dans ml/data/processed/, et rapport de synthèse.

Utilisable en script (`python ml/scripts/prepare_data.py`) ou en import
(les fonctions ci-dessous sont testées individuellement dans ml/tests/test_data.py).
"""

from __future__ import annotations

import argparse
import json
import random
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, UnidentifiedImageError

VALID_EXTENSIONS = {".jpg", ".jpeg", ".png"}
DEFAULT_SPLITS = {"train": 0.7, "val": 0.15, "test": 0.15}
MIN_IMAGES_PER_CLASS = 20
IMBALANCE_WARNING_RATIO = 3.0  # classe majoritaire / classe minoritaire au-delà duquel on alerte


@dataclass
class ValidationReport:
    valid: dict[str, list[Path]] = field(default_factory=dict)
    corrupt: dict[str, list[Path]] = field(default_factory=dict)

    def as_summary(self) -> dict:
        return {
            "classes": sorted(self.valid.keys()),
            "valid_counts": {c: len(paths) for c, paths in self.valid.items()},
            "corrupt_counts": {c: len(paths) for c, paths in self.corrupt.items()},
            "total_valid": sum(len(p) for p in self.valid.values()),
            "total_corrupt": sum(len(p) for p in self.corrupt.values()),
        }


def _is_readable_image(path: Path) -> bool:
    try:
        with Image.open(path) as img:
            img.verify()
        return True
    except (UnidentifiedImageError, OSError):
        return False


def validate_raw_dataset(raw_dir: Path) -> ValidationReport:
    """Parcourt raw_dir/<classe>/*.jpg, écarte les entrées corrompues ou au
    mauvais format, et lève une erreur si une classe est trop peu représentée.
    """
    report = ValidationReport()

    if not raw_dir.exists():
        raise FileNotFoundError(f"Dossier de données brutes introuvable : {raw_dir}")

    class_dirs = sorted(p for p in raw_dir.iterdir() if p.is_dir())
    if not class_dirs:
        raise ValueError(f"Aucune classe trouvée dans {raw_dir} (dossiers attendus par classe).")

    for class_dir in class_dirs:
        valid_paths: list[Path] = []
        corrupt_paths: list[Path] = []
        for file_path in sorted(class_dir.iterdir()):
            if file_path.suffix.lower() not in VALID_EXTENSIONS:
                continue
            if _is_readable_image(file_path):
                valid_paths.append(file_path)
            else:
                corrupt_paths.append(file_path)

        report.valid[class_dir.name] = valid_paths
        if corrupt_paths:
            report.corrupt[class_dir.name] = corrupt_paths

        if len(valid_paths) < MIN_IMAGES_PER_CLASS:
            raise ValueError(
                f"Classe '{class_dir.name}' insuffisamment représentée : "
                f"{len(valid_paths)} images valides (minimum {MIN_IMAGES_PER_CLASS})."
            )

    return report


def compute_class_imbalance(valid_by_class: dict[str, list[Path]]) -> dict:
    """Ratio classe majoritaire / classe minoritaire — un déséquilibre fort
    biaise le modèle vers les classes sur-représentées (voir ml/README.md :
    la classe `trash` est structurellement sous-représentée dans TrashNet)."""
    counts = {cls: len(paths) for cls, paths in valid_by_class.items() if paths}
    if not counts:
        return {"ratio": 0.0, "majority_class": None, "minority_class": None, "warning": False}

    majority_class = max(counts, key=counts.get)
    minority_class = min(counts, key=counts.get)
    ratio = counts[majority_class] / counts[minority_class]

    return {
        "ratio": round(ratio, 2),
        "majority_class": majority_class,
        "minority_class": minority_class,
        "warning": ratio > IMBALANCE_WARNING_RATIO,
    }


def split_dataset(
    valid_by_class: dict[str, list[Path]],
    ratios: dict[str, float] = DEFAULT_SPLITS,
    seed: int = 42,
) -> dict[str, dict[str, list[Path]]]:
    """Découpage stratifié : chaque classe est répartie selon les mêmes ratios,
    pour garantir que train/val/test restent représentatifs de chaque classe."""
    total_ratio = sum(ratios.values())
    if abs(total_ratio - 1.0) > 1e-6:
        raise ValueError(f"Les ratios de split doivent sommer à 1.0 (actuellement {total_ratio}).")

    rng = random.Random(seed)
    result: dict[str, dict[str, list[Path]]] = {split: {} for split in ratios}

    for class_name, paths in valid_by_class.items():
        shuffled = paths[:]
        rng.shuffle(shuffled)

        n = len(shuffled)
        n_train = int(n * ratios["train"])
        n_val = int(n * ratios["val"])

        result["train"][class_name] = shuffled[:n_train]
        result["val"][class_name] = shuffled[n_train : n_train + n_val]
        result["test"][class_name] = shuffled[n_train + n_val :]

    return result


def materialize_split(split_data: dict[str, dict[str, list[Path]]], processed_dir: Path) -> None:
    if processed_dir.exists():
        shutil.rmtree(processed_dir)

    for split_name, by_class in split_data.items():
        for class_name, paths in by_class.items():
            target_dir = processed_dir / split_name / class_name
            target_dir.mkdir(parents=True, exist_ok=True)
            for path in paths:
                shutil.copy2(path, target_dir / path.name)


def run(raw_dir: Path, processed_dir: Path, reports_dir: Path, seed: int = 42) -> dict:
    report = validate_raw_dataset(raw_dir)
    split_data = split_dataset(report.valid, seed=seed)
    materialize_split(split_data, processed_dir)

    summary = report.as_summary()
    summary["split_counts"] = {
        split: {cls: len(paths) for cls, paths in by_class.items()}
        for split, by_class in split_data.items()
    }
    summary["class_imbalance"] = compute_class_imbalance(report.valid)
    if summary["class_imbalance"]["warning"]:
        imbalance = summary["class_imbalance"]
        print(
            f"AVERTISSEMENT : déséquilibre des classes détecté — '{imbalance['majority_class']}' a "
            f"{imbalance['ratio']}x plus d'images que '{imbalance['minority_class']}'. "
            "Envisager un sur-échantillonnage ou une pondération de la perte à l'entraînement.",
            file=sys.stderr,
        )

    reports_dir.mkdir(parents=True, exist_ok=True)
    with open(reports_dir / "data_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Prépare le jeu de données TriPhoto (validation + split).")
    root = Path(__file__).resolve().parents[1]
    parser.add_argument("--raw-dir", type=Path, default=root / "data" / "raw" / "trashnet" / "dataset-resized")
    parser.add_argument("--processed-dir", type=Path, default=root / "data" / "processed")
    parser.add_argument("--reports-dir", type=Path, default=root / "reports")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    summary = run(args.raw_dir, args.processed_dir, args.reports_dir, seed=args.seed)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
