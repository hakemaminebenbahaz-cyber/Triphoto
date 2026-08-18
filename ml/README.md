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

## Résultat du dernier entraînement (10 epochs, seed 42, augmentation + 11 photos réelles)

- Accuracy validation (meilleure epoch, #9) : **82.0 %**
- Accuracy test (jeu isolé, jamais vu à l'entraînement) : **81.4 %**
- Porte de qualité (seuil 60 %) : **passée**

Voir `ml/reports/evaluation_report.json` pour le détail par classe et `ml/reports/confusion_matrix.png` pour la matrice de confusion.

### Itération 4 : essai de photos web, échec, retour arrière (feedback loop, méthode complète)

Une nouvelle photo réelle (verre à facettes sur fond blanc, style photo produit) a de nouveau été mal classée après l'itération 3 — "plastique" à 41 %, verre absent du top-3. Diagnostic : cette photo n'est ni une bouteille teintée (TrashNet) ni une photo prise à la main (itération 3), mais une troisième distribution encore différente (photo produit/stock, motif à facettes).

**Action tentée** : 21 photos de verre transparent collectées sur des banques d'images libres de droits (Wikimedia Commons, Openverse — licences CC0/BY/BY-SA), 15 retenues après tri visuel (6 écartées : verre teinté ancien de musée, macro trop abstraite, contenu opaque masquant le verre, scène trop chargée avec d'autres objets). Ajoutées à la classe `glass`, ré-entraînement complet.

**Résultat mesuré sur les 9 photos réelles tenues à l'écart de l'entraînement** (5 nouvelles + 4 de l'itération 3) : **1 correcte sur 9**. Pire : la confusion dominante s'est déplacée de `glass → paper` vers **`glass → metal`** (13 cas dans la matrice de confusion, contre 6 avant), probablement parce que les forts reflets spéculaires des photos "studio" professionnelles ressemblent visuellement au brillant d'un objet métallique — un nouveau raccourci appris par le modèle, pas une amélioration.

**Décision** : retour arrière. Les 15 photos web ont été retirées, le modèle a été ré-entraîné sur l'état de l'itération 3 (11 photos réelles uniquement), retrouvant exactement 81,4 % d'accuracy test. Conserver un correctif qui déplace un problème plutôt que de le résoudre n'est pas un progrès, même si l'intention était bonne.

**Enseignement retenu** : les photos "réelles" ne sont pas interchangeables. Une photo prise au téléphone dans des conditions d'usage réel (itération 3) et une photo issue d'une banque d'images professionnelle (itération 4) sont deux distributions différentes, malgré le même sujet apparent. La prochaine tentative d'amélioration de la classe `glass` devra continuer avec des photos prises dans les conditions réelles d'usage de l'application, pas des photos "propres" trouvées en ligne.

### Itération 3 : ajout de 11 photos réelles de verre transparent (feedback loop, C11/C20)

Un usager testant l'application en conditions réelles a signalé des erreurs sur du verre transparent tenu à la main (voir capture ci-dessous) : le modèle prédisait "papier" avec une confiance de 96 %. Diagnostic confirmé par inspection des données d'entraînement : la classe `glass` de TrashNet ne contient que des **bouteilles teintées** (brun, vert) photographiées en studio — jamais de verre transparent incolore. Un objet transparent laisse transparaître le fond, donnant une image globalement pâle et uniforme qui ressemble statistiquement à la classe `paper` (papier blanc sur fond clair) plutôt qu'à une bouteille de bière brune.

**Action** : 13 photos réelles de verre transparent collectées (téléphone, conditions réelles variées — fonds différents, avec/sans main, angles variés), 11 retenues après tri (2 écartées : il s'agissait en réalité d'une tasse en céramique opaque, pas de verre — les intégrer aurait introduit une erreur d'étiquetage). Ajoutées à la classe `glass`, ré-entraînement complet.

**Résultat mesuré sur une photo réelle jamais vue à l'entraînement** (tombée dans le jeu de validation par le découpage stratifié) : prédiction correcte "verre" à 73,7 % de confiance, contre une confiance de 96 % pour la mauvaise réponse ("papier") avant cet ajout.

**Contrepartie honnête** : l'accuracy globale sur le jeu de test TrashNet (composé à 100 % de photos "studio") baisse légèrement (83,9 % → 81,4 %). Avec seulement 11 photos ajoutées sur 2538, c'est un bruit statistique attendu, pas une régression réelle — et ça illustre un point important : optimiser pour ce jeu de test benchmark n'est pas rigoureusement identique à optimiser pour l'usage réel. La priorité donnée ici à la généralisation réelle plutôt qu'au score sur le benchmark est un choix assumé, pas un oubli.

### Itération 2 : effet de l'augmentation de données (sans nouvelles photos)

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

D'après `ml/reports/evaluation_report.json` sur le jeu de test (386 images) :

| Classe    | Precision | Recall | F1   |
|-----------|-----------|--------|------|
| cardboard | 0.93      | 0.87   | 0.90 |
| glass     | 0.88      | 0.68   | 0.77 |
| metal     | 0.71      | 0.85   | 0.77 |
| paper     | 0.80      | 0.89   | 0.84 |
| plastic   | 0.82      | 0.85   | 0.83 |
| trash     | 0.72      | 0.59   | 0.65 |

- **`trash` reste la classe la plus fragile** (F1 0.65, recall 0.59), pour les mêmes raisons qu'avant : catégorie la moins représentée (137 images) et intrinsèquement hétérogène. Avec seulement 22 exemples dans le jeu de test, ces chiffres restent statistiquement volatils.
- **`glass` gagne en precision (0.75→0.88) mais perd en recall (0.84→0.68)** après l'ajout des photos réelles : le modèle est maintenant plus prudent avant de dire "verre" (moins de faux positifs), mais rate davantage de vrais verres sur le jeu de test *studio* — cohérent avec le fait qu'il a appris à reconnaître une variante de verre (transparent) qu'il confondait auparavant avec autre chose, au prix d'un léger déséquilibre sur la distribution d'origine. Le vrai gain (reconnaître du verre transparent réel) est confirmé par le test direct sur photo réelle ci-dessus, pas visible dans cette seule métrique agrégée.
- **`metal` perd en precision (0.83→0.71)** : peut recevoir plus de faux positifs qu'avant — signal à surveiller si de nouvelles photos réelles de métal sont ajoutées plus tard.
- Dataset de taille modeste (2527 images) et toujours des photos "studio" à la base (fond uni, objet isolé) — l'augmentation de données réduit l'écart avec des photos prises à la main en conditions réelles, mais ne l'élimine pas complètement. Un vrai jeu de données de photos "terrain" annotées resterait la meilleure amélioration future.
- Pas de classe "organique" (voir plus haut) — assumé, pas caché.
