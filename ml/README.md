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

2. **`train.py`** (C12, C13) — backbone MobileNetV3-Small gelé + tête reclassée sur 6 sorties, optimiseur Adam sur la tête uniquement, 10 epochs par défaut. Le jeu d'entraînement passe par une **augmentation de données** (recadrage aléatoire, flip horizontal, jitter couleur, rotation ±15°) — jamais appliquée à val/test — pour réduire l'écart entre les photos "studio" de TrashNet et des photos prises à la main en conditions réelles (voir "Limites connues" ci-dessous). Sauvegarde le meilleur modèle (accuracy val la plus haute) en `.pt`, exporte en `.onnx` (consommé par l'API), écrit `ml/reports/train_history.json`.

3. **`evaluate.py`** (C12, C13) — évalue le modèle sauvegardé sur le jeu de test isolé, calcule accuracy + precision/recall/f1 par classe + matrice de confusion, écrit `ml/reports/evaluation_report.json` + `ml/reports/confusion_matrix.png`. `validate_against_threshold()` fait office de porte de qualité pour la CI (échec du pipeline si l'accuracy passe sous 60%).

## Résultat du dernier entraînement (10 epochs, seed 42, avec augmentation)

- Accuracy validation (meilleure epoch, #9) : **86.5 %**
- Accuracy test (jeu isolé, jamais vu à l'entraînement) : **83.9 %**
- Porte de qualité (seuil 60 %) : **passée**

Voir `ml/reports/evaluation_report.json` pour le détail par classe et `ml/reports/confusion_matrix.png` pour la matrice de confusion.

### Historique : effet de l'augmentation de données

Un premier modèle (5 epochs, sans augmentation) atteignait 79,7 % sur le même jeu de test. En usage réel (photos prises à la main, fond quelconque, hors du cadre "studio" de TrashNet), ce modèle se trompait nettement plus qu'attendu au vu de son accuracy de test — signe classique d'un **écart entre distribution d'entraînement et distribution réelle**, pas d'un bug. Ajouter de l'augmentation de données à l'entraînement (recadrage aléatoire, flip, jitter couleur, rotation) simule une partie de cette variabilité sans collecter de nouvelles données :

| Classe    | F1 avant (sans augmentation) | F1 après (avec augmentation) |
|-----------|:---:|:---:|
| cardboard | 0.86 | **0.91** |
| glass     | 0.73 | **0.80** |
| metal     | 0.80 | **0.85** |
| paper     | 0.87 | 0.84 |
| plastic   | 0.75 | **0.86** |
| trash     | 0.76 | 0.68 |
| **accuracy globale** | 79.7 % | **83.9 %** |

La confusion dominante précédente (verre classé "plastique" : 20 des 76 photos de verre du jeu de test) tombe à 8. La classe `plastic` gagnait des faux positifs par excès de confiance (precision 0.63) ; elle atteint maintenant 0.86.

## Limites connues (mesurées, pas supposées)

D'après `ml/reports/evaluation_report.json` sur le jeu de test (384 images) :

| Classe    | Precision | Recall | F1   |
|-----------|-----------|--------|------|
| cardboard | 0.95      | 0.87   | 0.91 |
| glass     | 0.75      | 0.84   | 0.80 |
| metal     | 0.83      | 0.87   | 0.85 |
| paper     | 0.84      | 0.84   | 0.84 |
| plastic   | 0.86      | 0.85   | 0.86 |
| trash     | 0.81      | 0.59   | 0.68 |

- **`trash` reste la classe la plus fragile** (F1 0.68, recall 0.59) et s'est même dégradée par rapport à avant (0.76). Deux causes plausibles : c'est la classe la moins représentée à l'entraînement (137 images vs 400-600 pour les autres), et c'est une catégorie "fourre-tout" par nature — hétérogène par construction, donc plus dure à cerner qu'une matière homogène comme le carton. Avec seulement 22 exemples dans le jeu de test, ces chiffres restent aussi statistiquement volatils (une poignée d'erreurs de plus/moins change beaucoup le pourcentage).
- Dataset de taille modeste (2527 images) et toujours des photos "studio" à la base (fond uni, objet isolé) — l'augmentation de données réduit l'écart avec des photos prises à la main en conditions réelles, mais ne l'élimine pas complètement. Un vrai jeu de données de photos "terrain" annotées resterait la meilleure amélioration future.
- Pas de classe "organique" (voir plus haut) — assumé, pas caché.
