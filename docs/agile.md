# Organisation agile — TriPhoto

## Contexte : agile en solo

Le projet est réalisé par un seul candidat, sans équipe technique. Une conduite agile "de manuel" (plusieurs rôles répartis sur plusieurs personnes, mêlée quotidienne entre pairs) n'a donc pas de sens telle quelle — mais les principes (cadence courte, visibilité du travail, rétrospective, priorisation continue) restent appliqués, avec des rôles explicitement endossés par la même personne plutôt qu'ignorés.

| Rôle Scrum | Qui, ici |
|---|---|
| Product Owner | Le candidat, en se plaçant du point de vue du commanditaire fictif (la collectivité) pour prioriser le backlog. |
| Développeur | Le candidat. |
| Scrum Master / facilitateur | Le candidat, au moment des rituels (voir ci-dessous) — rôle explicitement "changé de casquette", documenté dans le journal de sprint plutôt que simulé. |

## Méthode et outils

- **Kanban** (plutôt que Scrum complet) : mieux adapté à un flux solo qu'un cadre à cérémonies multiples pensées pour un collectif.
- **Tableau** : GitHub Projects (colonnes `À faire` / `En cours` / `Fait`), lié au dépôt `TriPhoto`.
- **Backlog** : ce fichier + les issues GitHub du dépôt (une issue = un item du backlog ci-dessous).
- **Suivi de la conformité C9–C19** : grille de conformité dédiée (44 livrables), utilisée comme backlog technique détaillé en complément du backlog fonctionnel ci-dessous.

## Rituels (adaptés au solo)

| Rituel | Fréquence | Forme |
|---|---|---|
| Planification de sprint | Début de chaque sprint (~1 semaine) | Choix des items du backlog à traiter, consigné dans ce fichier. |
| Point quotidien | Chaque session de travail | Une ligne dans le journal de sprint (`## Journal`) : fait / bloquant / prochaine étape. |
| Revue de sprint | Fin de sprint | Démonstration à soi-même (ou à un tiers si disponible) des items terminés — capture d'écran ou commande exécutée comme preuve. |
| Rétrospective | Fin de sprint | 2-3 lignes : ce qui a bien marché, ce qui a coûté plus cher que prévu, ce qui change au sprint suivant. |

## Sprint 1 — 8 août 2026 → 15 août 2026

**Objectif de sprint** : backend complet et démontrable (API + modèle entraîné) + squelette front fonctionnel.

### Backlog du sprint

| Item | Compétences | Statut | Date |
|---|---|---|---|
| Scaffolding repo + API FastAPI (auth JWT, /predict, /health) | C9, C10 | Fait | 08/08 |
| Dataset TrashNet préparé (validation, split stratifié) | C12 | Fait | 08/08 |
| Entraînement + évaluation du modèle (79,7 % accuracy) | C12, C13 | Fait | 08/08 |
| Câblage API ↔ modèle ONNX réel | C9, C11 | Fait | 08/08 |
| App React (formulaire, accessibilité, appel API) | C14, C17 | Fait | 08/08 |
| Vérification end-to-end en navigateur réel | — | Fait | 08/08 |
| Pipelines CI/CD modèle + application | C13, C18, C19 | Fait | 08/08 |
| User stories, architecture, agile, accessibilité, RGPD | C14, C15, C16 | En cours | 08/08 |
| Monitorage du modèle (dashboard + alertes réelles) | C11 | À faire | — |
| Renouvellement de token vérifié côté front en conditions d'expiration réelle | C10 | À faire | — |
| PoC déployée en pré-production (hors localhost) | C15 | À faire | — |
| Kanban GitHub Projects créé et lié aux issues | C16 | À faire | — |
| Répétition du script de soutenance E3 (15-20') et E4 (20') | — | À faire | — |

### Journal

- **08/08** — Sprint démarré. Choix du projet (classification déchets par photo) après comparaison avec régression prix immobilier. Repo créé indépendamment (pas de réutilisation du code ObRail). Backend + front + CI construits et vérifiés fonctionnels en conditions réelles (photo réelle → prédiction correcte affichée dans le navigateur). Aucun bloquant majeur ; point de vigilance noté : la CI n'a pas encore été exécutée sur GitHub (seulement en local), à valider au premier push.

### Rétrospective (à date)

- **Ce qui a bien marché** : réutiliser la structure éprouvée sur un premier projet (tests, CI, séparation api/ml/app) a permis d'aller vite sans sacrifier la rigueur.
- **Ce qui a coûté plus cher que prévu** : les incompatibilités de versions (exporteur ONNX de PyTorch, Node vs Vite 8, esbuild vulnérable) ont pris du temps à diagnostiquer — à anticiper en fixant des versions dès le départ plutôt qu'en prenant les dernières par défaut.
- **Pour le sprint suivant** : traiter en priorité les items encore ouverts qui touchent à des critères de conformité explicites (monitorage réel, PoC déployée) plutôt que du polish, puisque ce sont eux qui déterminent la note.
