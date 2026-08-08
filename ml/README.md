# TriPhoto — ML

Classifieur de déchets par photo. Transfer learning sur MobileNetV3-Small (poids ImageNet), tête de classification ré-entraînée sur 6 classes.

## Dataset

[TrashNet](https://huggingface.co/datasets/garythung/trashnet) (Gary Thung & Mindy Yang, licence MIT) — 2527 photos de déchets isolés sur fond uni, réparties en 6 classes : `cardboard`, `glass`, `metal`, `paper`, `plastic`, `trash`.

Téléchargement (dataset non versionné dans le repo — voir `.gitignore`) :
```bash
curl -L "https://huggingface.co/datasets/garythung/trashnet/resolve/main/dataset-resized.zip" -o ml/data/raw/dataset-resized.zip
cd ml/data/raw && unzip dataset-resized.zip -d trashnet && rm dataset-resized.zip
```
Résultat attendu : `ml/data/raw/trashnet/dataset-resized/<classe>/*.jpg`.

### Correspondance des classes (dataset → étiquette exposée par l'API)

| Dossier TrashNet | Label API   | Consigne de tri              |
|-------------------|-------------|-------------------------------|
| cardboard          | carton      | Bac jaune (tri sélectif)      |
| glass               | verre       | Bac à verre                   |
| metal               | metal       | Bac jaune (tri sélectif)      |
| paper               | papier      | Bac jaune (tri sélectif)      |
| plastic             | plastique   | Bac jaune (tri sélectif)      |
| trash               | poubelle_generale | Bac ordures ménagères   |

Pas de classe "organique" : TrashNet ne couvre pas les biodéchets — on ne prétend pas classifier ce qu'on n'a jamais entraîné.

## Pipeline

1. **`prepare_data.py`** (C12) — valide chaque image (ouverture PIL, rejet des fichiers corrompus), vérifie qu'aucune classe n'est sous-représentée (< 20 images), découpe en train/val/test (70/15/15, stratifié par classe, seed fixe pour la reproductibilité), matérialise dans `ml/data/processed/`, écrit `ml/reports/data_summary.json`.

2. **`train.py`** (C12, C13) — backbone MobileNetV3-Small gelé + tête reclassée sur 6 sorties, optimiseur Adam sur la tête uniquement, 5 epochs par défaut. Sauvegarde le meilleur modèle (accuracy val la plus haute) en `.pt`, exporte en `.onnx` (consommé par l'API), écrit `ml/reports/train_history.json`.

3. **`evaluate.py`** (C12, C13) — évalue le modèle sauvegardé sur le jeu de test isolé, calcule accuracy + precision/recall/f1 par classe + matrice de confusion, écrit `ml/reports/evaluation_report.json` + `ml/reports/confusion_matrix.png`. `validate_against_threshold()` fait office de porte de qualité pour la CI (échec du pipeline si l'accuracy passe sous 60%).

## Résultat du dernier entraînement (5 epochs, seed 42)

- Accuracy validation : **80.1 %**
- Accuracy test (jeu isolé, jamais vu à l'entraînement) : **79.7 %**
- Porte de qualité (seuil 60 %) : **passée**

Voir `ml/reports/evaluation_report.json` pour le détail par classe et `ml/reports/confusion_matrix.png` pour la matrice de confusion.

## Limites connues (mesurées, pas supposées)

D'après `ml/reports/evaluation_report.json` sur le jeu de test (384 images) :

| Classe    | Precision | Recall | F1   |
|-----------|-----------|--------|------|
| cardboard | 0.91      | 0.82   | 0.86 |
| paper     | 0.84      | 0.90   | 0.87 |
| trash     | 0.80      | 0.73   | 0.76 |
| metal     | 1.00      | 0.66   | 0.80 |
| glass     | 0.78      | 0.68   | 0.73 |
| plastic   | 0.63      | 0.90   | 0.75 |

- **Confusion dominante : verre → plastique.** 20 des 76 photos de verre du jeu de test sont classées "plastique" (voir `confusion_matrix.png`) — probablement des bouteilles transparentes que le modèle confond par la forme plutôt que la matière. C'est la principale source d'erreur du modèle actuel, à montrer honnêtement en soutenance plutôt qu'à espérer que le jury ne pose pas la question.
- **`metal` a un bon recall faible (0.66) malgré une precision parfaite (1.00)** : quand le modèle dit "métal" il a toujours raison, mais il rate 1 métal sur 3 (probablement confondu avec du verre ou du plastique brillant).
- Dataset de taille modeste (2527 images) et fond uni pour chaque photo — un déchet photographié dans un environnement encombré (poubelle, sol, main) sera probablement moins bien reconnu en usage réel que sur ce jeu de test.
- Classe `trash` sous-représentée à l'entraînement (137 images vs 400-600 pour les autres), mais ses métriques restent dans la moyenne — la sous-représentation n'est pas ici le facteur le plus limitant.
