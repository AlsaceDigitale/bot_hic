# Messages automatiques (MSG_AUTO)

Ce document décrit la fonctionnalité de publication automatique de messages (cog `AutoMessageCog`). Il explique : le canal par défaut, le comportement du bot (fréquence, réactions), le format attendu des messages postés dans le canal configuré pour les messages automatiques, et quelques conseils de dépannage.

## Canal par défaut

- Variable d'environnement : `BOT_CHANNEL_MSG_AUTO`
- Valeur par défaut : `msg_auto` (si non configuré)
- Remarque : le cog recherche le canal texte portant ce nom pour lire la "base" des messages planifiés.

## Comportement du bot

- Le bot charge tous les messages présents dans le canal configuré au démarrage et chaque fois qu'un message est créé, édité ou supprimé dans ce canal.
- Le bot ignore (ne traite pas) les messages qui ont déjà des réactions (len(message.reactions) > 0). Cela permet de marquer manuellement des messages comme exclus.
- Intervalle de vérification : la tâche `send_msg_auto` s'exécute toutes les 30 secondes (loop `seconds=30.0`).
- Résolution temporelle : le bot compare la date/heure planifiée arrondie à la minute (il calcule `now = datetime.now().replace(second=0)`), donc la précision est à la minute.
- À l'envoi : pour chaque message planifié arrivé à son minute, le bot construit un embed (couleur et titre optionnels) et l'envoie dans les salons ciblés.
- Après publication, le bot ajoute la réaction `👍` sur le message original dans le canal `MSG_AUTO` pour indiquer qu'il a été publié.

## Réactions utilisées pour indiquer l'état d'un message dans le canal `MSG_AUTO`

- `👎` : erreur de parsing (format invalide) — le message n'a pas été accepté.
- `⏲` : message daté dans le passé (la date/heure indiquée est déjà atteinte) — le message est ignoré.
- `☠️` : exception inattendue lors du parsing — le message n'a pas pu être traité.
- `👍` : message publié (ajouté par le bot après envoi aux salons ciblés).

## Format attendu d'un message dans le canal `MSG_AUTO`

Le message doit comporter deux parties séparées exactement par la ligne :

\n-----\n

1) Un bloc d'en-têtes (headers) composé de lignes `Clé: Valeur` (une par ligne).
2) Une ligne contenant exactement `-----` entourée de sauts de ligne (séparateur).
3) Le corps (body) du message à publier (peut être multi‑ligne).

Exemple minimal (les caractères `\n` ci‑dessous représentent des nouvelles lignes) :

Date: 25/11/2025 14:30
Salons: <#123456789012345678>
Couleur: FFAABB
Titre: Rappel important

-----

Ceci est le texte de l'annonce. Il peut s'étendre sur plusieurs lignes et contenir du Markdown.

Important : la séparation doit être exactement une ligne contenant `-----` entourée d'un saut de ligne avant et après (soit la chaîne `"\n-----\n"`).

### En‑têtes reconnus (insensibles à la casse des clés) et comportement

- `Date: DD/MM/YYYY HH:MM`
  - Obligatoire. Format exact : jour/mois/année heure:minutes (24h). Exemple : `25/11/2025 14:30`.
  - Le bot utilise l'heure système de la machine où il tourne (appel à `datetime.now()`) et compare à la minute près. Assurez‑vous que l'horloge et le fuseau horaire de l'hôte sont corrects.

- `Salons: <#CHANNEL_ID>` ou `Salons: <#ID1> <#ID2> ...`
  - Obligatoire. Liste de mentions de salons Discord (format `<#123...>`), séparées par des espaces si plusieurs.
  - Le bot extrait l'ID numérique des mentions et enverra l'embed dans chacun de ces salons si le salon existe sur la guild.

- `Couleur: RRGGBB` ou `Couleur: 12345`
  - Optionnel. Peut être une valeur hex (6 caractères hexadécimaux, exemple `FFAABB`) ou un entier non négatif (ex : `2013674`).
  - Si hex fourni, il est converti en entier pour Discord (`int("0x" + value, 0)`).

- `Titre: texte`
  - Optionnel. Si présent, sera utilisé pour `embed.title`.

- Autres en‑têtes
  - Tout autre `Clé: Valeur` est stocké en tant que `clé` (en minuscule) et peut être utilisé par la cog ; toutefois, seules `date`, `salons`, `couleur`, `titre` et `body` sont explicitement exploitées pour la publication.

### Règles et bonnes pratiques

- Le message ne doit contenir aucune réaction au moment du parsing : si des réactions sont présentes, le message est ignoré.
- Assurez‑vous que la date est dans le futur : si la date est déjà passée, le bot réagira `⏲` et n'ajoutera pas le message à la file.
- Utilisez `Salons:` avec la forme de mention `<#ID>` (copier la mention de salon depuis Discord garantit le bon format).
- Pour modifier la planification d'un message : éditez le message dans le canal `MSG_AUTO` (la cog recharge automatiquement la liste après édition). Pour retirer l'annonce planifiée sans la publier, ajoutez manuellement une réaction sur le message (puisque le bot ignore les messages ayant des réactions).

## Exemple complet

Voici un exemple concret à coller dans le canal `msg_auto` :

Date: 01/12/2025 09:00
Salons: <#987654321098765432> <#123456789012345678>
Couleur: FF9900
Titre: Petit rappel

-----

Bonjour à tous,

Petit rappel pour la session de ce matin à 09:15. Merci d'être à l'heure !

---

## Dépannage rapide

- Si votre message reçoit `👎` : vérifiez le format des headers et la présence exacte de la ligne séparatrice `-----`.
- Si votre message reçoit `⏲` : votre date est déjà atteinte (ou dans le passé). Ré-enregistrez avec une date ultérieure.
- Si rien ne se passe au moment attendu : vérifiez que le bot a accès aux salons ciblés (permissions `Send Messages`), que les IDs de salon sont corrects et que le bot tourne (tâche active).
- Pour tests locaux : poster un message avec une date à la minute suivante et surveiller les réactions/les publications.

