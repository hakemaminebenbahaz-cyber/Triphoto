# Protection des données — TriPhoto

Note courte : TriPhoto ne gère pas de base de données à caractère personnel au sens du bloc 1 (C4, traité sur le projet ObRail) — mais l'application manipule des photos qui peuvent, incidemment, contenir des éléments identifiants. Ce document répond par avance à la question qu'un jury pose systématiquement : *"que faites-vous des photos envoyées ?"*

## Données traitées

| Donnée | Nature | Traitement |
|---|---|---|
| Photo du déchet | Peut incidemment contenir des éléments identifiants (reflet, arrière-plan d'un intérieur) | Reçue par l'API, chargée en mémoire pour le prétraitement et l'inférence, **jamais écrite sur disque ni journalisée**. Rejetée de la mémoire dès la réponse envoyée. |
| Token d'authentification (JWT) | Donnée technique applicative, pas liée à une personne physique — l'authentification protège l'accès à l'API entre l'application et le modèle, pas un compte usager | Signé, à durée de vie courte (15 min pour l'access token), jamais stocké côté serveur (pas de session persistée). |
| Métriques de monitorage (C11) | Techniques (latence, code retour, accuracy) | Ne doivent contenir ni photo ni fragment de photo — à vérifier explicitement dans la configuration de l'outil de monitorage retenu. |

## Base légale (dans le contexte fictif du commanditaire)

Intérêt légitime de la collectivité à fournir un service d'aide au tri sélectif, sans collecte de compte usager ni de données au-delà de la photo transmise volontairement pour l'usage immédiat du service.

## Minimisation

- Aucune création de compte, aucun identifiant personnel demandé à l'usager final.
- Aucune conservation de la photo au-delà du traitement de la requête (pas de dossier d'upload, pas de table `predictions` historisant les images).
- Si un historique des prédictions devait être ajouté à l'avenir (fonctionnalité hors périmètre actuel), il devrait stocker le résultat (label, date) sans la photo elle-même, ou avec un consentement explicite et une durée de conservation définie.

## Droits des personnes concernées

Comme aucune donnée personnelle n'est conservée au-delà du traitement immédiat de la requête, il n'existe pas de droit d'accès/rectification/suppression à exercer a posteriori — ce point doit néanmoins être explicable clairement à l'oral plutôt que découvert en Q/R.

## Point de vigilance pour la suite du projet

Si un outil de monitorage tiers est intégré (C11) et journalise les requêtes HTTP par défaut (ex. logs bruts d'un reverse proxy), vérifier qu'il n'enregistre pas le corps des requêtes `POST /predict` (qui contient la photo) — sinon la garantie "aucune conservation" ci-dessus serait rompue silencieusement par l'outillage d'infra plutôt que par le code applicatif.
