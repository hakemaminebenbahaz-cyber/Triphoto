# TriPhoto

Estimation instantanée du type de déchet (verre / plastique / carton / métal / organique / poubelle générale) à partir d'une photo, pour aider les usagers d'une collectivité à trier correctement.

Projet réalisé dans le cadre de la certification **Développeur en Intelligence Artificielle (RNCP37827)** — épreuves E3 (C9-C13, modèle & MLOps) et E4 (C14-C19, application).

## Contexte

Commanditaire fictif : une collectivité en charge de la gestion des déchets souhaite un outil accessible au grand public pour réduire les erreurs de tri, à partir d'une simple photo prise avec un smartphone.

## Structure du repo

```
TriPhoto/
├── api/            # API REST FastAPI qui expose le modèle (C9, C10)
├── ml/             # Préparation des données, entraînement, évaluation, tests du modèle (C11, C12, C13)
├── app/            # Application front-end (upload photo → résultat) (C14-C19)
├── monitoring/      # Config du monitorage du modèle (C11)
├── docs/           # Specs fonctionnelles, architecture, agile, accessibilité (C14-C16)
└── .github/workflows/  # Pipelines CI/CD modèle et application (C13, C18, C19)
```

## Démarrage rapide

### API
Toutes les commandes s'exécutent **depuis la racine du repo** (les imports sont en `api.xxx`) :
```bash
python -m venv .venv-api && .venv-api\Scripts\activate
pip install -r api/requirements.txt
uvicorn api.main:app --reload
pytest api/tests
```
Doc interactive une fois lancée : http://127.0.0.1:8000/docs

### ML
```bash
cd ml
pip install -r requirements.txt
python scripts/prepare_data.py
python scripts/train.py
python scripts/evaluate.py
```

### App
```bash
cd app
npm install
npm run dev
```

## État d'avancement

Voir la grille de conformité E3/E4 (compétences C9-C19) pour le suivi détaillé des livrables.
