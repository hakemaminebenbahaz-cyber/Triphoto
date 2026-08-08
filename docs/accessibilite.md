# Accessibilité — TriPhoto

Référentiel suivi : **WCAG 2.1, niveau AA** (recommandations internationales, cohérentes avec le RGAA français dont elles sont la base).

## Objectifs retenus et mise en œuvre

| Critère WCAG | Objectif | Mise en œuvre dans TriPhoto |
|---|---|---|
| 1.1.1 Contenu non textuel | Toute image porte une alternative textuelle | L'aperçu de la photo uploadée a un `alt` dynamique décrivant le fichier sélectionné (`App.tsx`). |
| 1.3.1 Information et relations | Les champs de formulaire sont structurés sémantiquement | `<label htmlFor="photo-input">` explicitement associé au `<input>`, pas de `placeholder` utilisé comme seul label. |
| 1.4.3 Contraste (minimum) | Ratio de contraste ≥ 4.5:1 pour le texte courant | Palette définie avec `--ink` sur `--bg`/`--surface` vérifiée manuellement (voir `app/src/index.css`) ; à re-vérifier avec un outil automatisé (axe/Lighthouse) avant la soutenance. |
| 1.4.1 Utilisation de la couleur | L'information n'est jamais donnée par la couleur seule | Le nom du bac est toujours écrit en toutes lettres à côté du résultat, jamais représenté uniquement par une pastille colorée. |
| 2.1.1 Clavier | Toutes les fonctionnalités sont utilisables au clavier | Champ de fichier, boutons "Identifier" et "Recommencer" sont des éléments natifs (`<input>`, `<button>`) nativement activables au clavier. |
| 2.4.7 Visibilité du focus | Le focus clavier est visuellement identifiable | `:focus-visible` stylé explicitement (contour 2px, couleur d'accent) sur les champs et boutons — pas de `outline: none` sans remplacement. |
| 4.1.3 Messages de statut | Les changements de contenu sont perçus sans déplacement du focus | Zone de résultat en `role="status" aria-live="polite"` : le résultat de la prédiction est annoncé automatiquement par les lecteurs d'écran dès qu'il apparaît. Le message d'erreur utilise `role="alert"` pour une annonce plus immédiate. |
| 3.3.1 / 3.3.3 Identification et suggestion des erreurs | Les erreurs sont explicites et actionnables | Messages d'erreur en français simple ("Format d'image non supporté. Utilisez une photo JPEG, PNG ou WebP."), jamais de code d'erreur brut affiché à l'usager. |

## Ce qui reste à vérifier avant la soutenance

- [ ] Audit automatisé (axe DevTools ou Lighthouse) sur la page déployée, pas seulement en développement local.
- [ ] Test de navigation complète au clavier seul (Tab / Shift+Tab / Entrée / Échap), sans souris, en conditions réelles.
- [ ] Test avec un lecteur d'écran réel (NVDA sous Windows, gratuit) sur le parcours complet : sélection de photo → soumission → annonce du résultat.
- [ ] Vérification du zoom navigateur à 200 % sans perte de contenu ni de fonctionnalité (reflow).

## Accessibilité de la documentation

Les documents transmis aux parties prenantes (rapports, cette documentation) suivent les recommandations de structuration de l'association Valentin Haüy : titres hiérarchisés (`#`, `##`, `###`), pas d'information encodée uniquement par la mise en forme visuelle, tableaux avec en-têtes explicites plutôt que des captures d'écran de tableaux.
