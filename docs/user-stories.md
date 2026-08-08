# User stories — TriPhoto

Commanditaire fictif : une collectivité en charge de la gestion des déchets. Persona principal : un usager, potentiellement non technophile, qui hésite devant sa poubelle.

Chaque critère d'accessibilité est écrit comme un critère d'acceptation à part entière (C14), pas ajouté après coup.

---

## US-01 — Identifier un déchet par photo

**En tant qu'** usager, **je veux** prendre en photo un déchet et obtenir instantanément une réponse, **afin de** savoir dans quel bac le jeter sans avoir à chercher dans un guide de tri.

**Contexte** : l'usager est chez lui ou dans un lieu public, avec un smartphone ou un ordinateur avec webcam, souvent dans une situation d'urgence ("je dois jeter ça maintenant").

**Scénarios** :
- Étant donné une photo nette d'un déchet isolé, quand l'usager la soumet, alors le nom de la matière et la consigne de tri s'affichent en moins de 5 secondes.
- Étant donné un fichier dans un format non supporté (ex. `.heic`, `.pdf`), quand l'usager le soumet, alors un message explicite indique les formats acceptés (JPEG, PNG, WebP) sans jargon technique.
- Étant donné une photo vide ou corrompue, quand l'usager la soumet, alors un message clair l'invite à réessayer avec une autre photo.

**Critères d'acceptation** :
- [ ] Le résultat affiche : la matière identifiée, la consigne de tri (nom du bac), le niveau de confiance du modèle.
- [ ] Le champ de sélection de fichier est accessible au clavier (`Tab`, `Entrée`/`Espace`) et correctement annoncé par un lecteur d'écran (`<label>` associé, pas de `placeholder` seul).
- [ ] Le résultat est annoncé automatiquement aux technologies d'assistance via une zone `aria-live="polite"` — l'usager n'a pas besoin de naviguer pour découvrir la réponse.
- [ ] Le contraste texte/fond du résultat respecte au moins le niveau AA des WCAG 2.1 (ratio ≥ 4.5:1 pour le texte courant).
- [ ] Aucune information n'est communiquée uniquement par la couleur (le nom du bac est toujours écrit en toutes lettres, jamais juste une pastille colorée).

---

## US-02 — Comprendre les limites de la réponse

**En tant qu'** usager, **je veux** voir le niveau de confiance de la prédiction, **afin de** savoir si je dois faire confiance à la réponse ou vérifier moi-même.

**Scénarios** :
- Étant donné une prédiction avec une confiance inférieure à 60 %, quand le résultat s'affiche, alors le pourcentage de confiance reste visible et lisible (pas de faux sentiment de certitude).

**Critères d'acceptation** :
- [ ] Le pourcentage de confiance est toujours affiché à côté de la réponse, jamais masqué ou minimisé visuellement au point d'être illisible (taille de police ≥ 0.85rem, contraste AA).
- [ ] Le texte reste en français simple, sans terme technique ("confiance du modèle", pas "score de vraisemblance softmax").

---

## US-03 — Recommencer facilement

**En tant qu'** usager, **je veux** pouvoir soumettre une nouvelle photo sans recharger la page, **afin de** trier plusieurs déchets à la suite rapidement.

**Critères d'acceptation** :
- [ ] Un bouton "Recommencer" réinitialise le formulaire, l'aperçu et le résultat sans rechargement de page.
- [ ] Le focus clavier est géré proprement après réinitialisation (pas de perte de focus qui obligerait à retabuler depuis le haut de la page).
- [ ] Le bouton "Recommencer" n'apparaît que lorsqu'il est pertinent (une photo a été choisie ou un résultat existe) — pas de bouton mort à l'écran.

---

## US-04 — Accéder au service sans compte

**En tant qu'** usager, **je veux** utiliser le service sans créer de compte, **afin de** ne pas être freiné par une inscription pour un besoin ponctuel.

**Contexte technique** : l'authentification (C9, C10) protège l'accès à l'API entre l'application et le modèle — elle n'est jamais exposée à l'usager final, qui n'a ni identifiant ni mot de passe à saisir.

**Critères d'acceptation** :
- [ ] Aucun champ d'identification n'est visible dans l'interface usager.
- [ ] En cas d'échec d'authentification technique (API indisponible, token invalide), le message affiché à l'usager reste compréhensible ("Service temporairement indisponible, réessayez.") — jamais une trace technique brute (stack trace, code HTTP).

---

## Hors périmètre (assumé, à mentionner en soutenance)

- Pas de compte utilisateur, pas d'historique de recherches, pas de géolocalisation des points de collecte — le périmètre reste volontairement celui d'un outil d'aide à la décision immédiate, pas d'une application de gestion des déchets complète.
- Pas de classe "biodéchets/organique" (voir `ml/README.md`) — assumé et communiqué à l'usager plutôt que deviné silencieusement.
