# BOT COMMANDS

Ce document recense les commandes du bot, regroupées par domaine. Pour chaque commande : signature, paramètres et notes (permissions, comportement particulier).

Remarque : les noms de commandes sont invoqués avec le préfixe configuré (`BOT_PREFIX`, par défaut `!`). Certaines commandes requièrent des rôles spéciaux (vérifiés par des checks comme `is_support_user` ou `is_support_or_supercoach_user`).

---

## Utilitaires (extensions.utils)

- crash_log
  - Usage : `!crash_log`
  - Paramètres : aucun
  - Description : envoie un message de test dans le canal de log du bot et lance un test d'exception (pour vérifier le traitement des erreurs). Requiert les droits de support (`is_support_user`).

- show_settings
  - Usage : `!show_settings`
  - Paramètres : aucun
  - Description : affiche la configuration courante (valeurs issues de `Settings`). Requiert `is_support_user`.

- show_categories
  - Usage : `!show_categories`
  - Paramètres : aucun
  - Description : liste les noms de catégories présentes sur la guild. Requiert `is_support_user`.

- purge
  - Usage : `!purge [DD/MM/YYYY]`
  - Paramètres : (optionnel) date au format `JJ/MM/AAAA`. Si omise, utilise la date courante.
  - Description : supprime les messages du canal (canal texte / news) postérieurs ou égaux à la date indiquée. Requiert `is_support_user`.

---

## Administration (extensions.admin)

- admin
  - Usage : `!admin`
  - Paramètres : aucun
  - Description : vérifie localement si l'utilisateur possède le rôle admin configuré (`BOT_ADMIN_ROLE`) et réagit au message (succès / échec). Accessible uniquement aux utilisateurs marqués comme support (`is_support_user`).

---

## Aide (extensions.help)

- aide
  - Usage : `!aide`
  - Paramètres : aucun
  - Description : envoie un embed d'aide contenant des informations utiles, mentions de rôles (`FACILITATEUR`, `ORGA`...), et liens (depuis `BOT_HELP_LINKS`).

- orga
  - Usage : `!orga`
  - Paramètres : aucun
  - Description : notifie le rôle organisateur (configuré via `BOT_ORGA_ROLE`) dans le canal d'aide. Ajoute une réaction de succès.

- coach
  - Usage : `!coach`
  - Paramètres : aucun
  - Description : notifie le rôle coach (configuré via `BOT_COACH_ROLE`) dans le canal d'aide. Ajoute une réaction de succès.

- support
  - Usage : `!support`
  - Paramètres : aucun
  - Description : notifie le rôle admin/support (configuré via `BOT_ADMIN_ROLE`) dans le canal de support technique. Ajoute une réaction de succès.

---

## Planning (extensions.planning)

- planning (alias: agenda)
  - Usage : `!planning [vendredi|samedi|dimanche|semaine]`
  - Paramètres : période optionnelle (`vendredi`, `samedi`, `dimanche`, `semaine`)
  - Description : récupère le PDF du planning depuis `EVENT_PLANNING_URL`, extrait le texte et envoie les sections pertinentes en DM à l'utilisateur. Affiche aussi le lien du PDF et l'icône (`EVENT_ICON_URL`).

---

## Sondages (extensions.poll)

- new_poll
  - Usage : `!new_poll "question" [maxvotes] "opt1" "opt2" ...`
  - Paramètres :
    - question (str) : la question du sondage (entourée de guillemets si contenant des espaces)
    - maxvotes (int, optionnel) : nombre maximum de votes par participant (défaut = 1)
    - options (str...) : liste d'options (au moins 2)
  - Description : crée un sondage dans le canal réservé aux votes. Seuls les utilisateurs avec `is_support_user` et (en pratique) les admins configurés peuvent l'utiliser. Le bot ajoute les réactions correspondantes et indique l'ID de message (utilisé pour fermer ou détruire).

- reset_poll
  - Usage : `!reset_poll <id>`
  - Paramètres : id (int) : identifiant du message sondage
  - Description : remet à zéro les réactions d'un sondage (efface puis rajoute les réactions). Requiert `is_support_user` et le rôle admin configuré.

- destroy_poll
  - Usage : `!destroy_poll <id>`
  - Paramètres : id (int)
  - Description : supprime définitivement le message identifié par `id`. Requiert `is_support_user` et le rôle admin configuré.

- close_poll
  - Usage : `!close_poll <id>`
  - Paramètres : id (int)
  - Description : clôture un sondage (compile les résultats, remet les réactions à zéro, édite le message pour afficher le résultat final). Requiert `is_support_user` et le rôle admin configuré.

Notes : le comportement de vote (limite de votes, acceptation d'emojis) dépend du contenu de l'embed et des constantes définies dans `PollCog`.

---

## Équipes (extensions.team)

- teamadd
  - Usage : `!teamadd <@EquipeRole> @membre1 [@membre2 ...]`
  - Paramètres :
    - nom_de_lequipe (discord.Role) : rôle de l'équipe (mention/objet Role)
    - members (list of discord.Member) : membres à ajouter (mentions)
  - Description : ajoute les membres indiqués au rôle d'équipe. Requiert `is_support_user` et que l'appelant ait le rôle admin (`BOT_ADMIN_ROLE`). Le nom du rôle doit commencer par `BOT_TEAM_PREFIX`.

- teamremove
  - Usage : `!teamremove <@EquipeRole> @membre1 [@membre2 ...]`
  - Paramètres : idem `teamadd`
  - Description : retire les rôles d'équipe aux membres indiqués. Requiert `is_support_user` et rôle admin.

- teamlist
  - Usage : `!teamlist`
  - Paramètres : aucun
  - Description : liste tous les rôles dont le nom commence par `BOT_TEAM_PREFIX`. Requiert `is_support_user` et rôle admin.

- teamdown
  - Usage : `!teamdown <nom_de_lequipe|mention_de_role>`
  - Paramètres : nom_de_lequipe (str) : soit le nom du rôle, soit une mention (le code tente d'accepter une forme `"<@...>"`)
  - Description : supprime un rôle d'équipe, retire le rôle aux membres, et supprime les canaux textuels / vocaux associés. Requiert `is_support_user` et rôle admin.

- teamup
  - Usage : `!teamup <nom_de_lequipe> @chef_de_projet @membre1 [@membre2 ...]`
  - Paramètres :
    - nom_de_lequipe (str)
    - chef_de_projet (discord.Member)
    - members (list of discord.Member)
  - Description : crée le rôle d'équipe, crée un canal textuel et vocal dans la catégorie configurée (`BOT_TEAM_CATEGORY`), assigne le chef de projet et les membres. Requiert `is_support_user` et rôle admin.

- teamcoachadd
  - Usage : `!teamcoachadd <@EquipeRole> @membre`
  - Paramètres : nom_de_lequipe (discord.Role), member (discord.Member)
  - Description : ajoute un coach à une équipe. Requiert `is_support_or_supercoach_user`.

- teamcoachremove
  - Usage : `!teamcoachremove <@EquipeRole> @membre`
  - Paramètres : idem
  - Description : retire un coach d'une équipe. Requiert `is_support_or_supercoach_user`.

- teamapi
  - Usage : `!teamapi`
  - Paramètres : aucun
  - Description : récupère la liste des équipes depuis l'API configurée (`BOT_URL_API` ➜ `/api/project-teams/`) et crée les rôles/canaux/membres correspondant aux équipes de l'événement (`EVENT_CODE`).

---

## Vidéo (extensions.video)

- video
  - Usage : `!video <url> [message]`
  - Paramètres :
    - url (str) : lien vers la vidéo (doit ressembler à une URL)
    - message (str, optionnel) : description/message associé
  - Description : enregistre et publie un lien vidéo dans le canal `videos` (le bot vérifie également l'accès au lien). L'utilisateur doit être membre d'une équipe dont le rôle commence par `Equipe-Défi-` et exécuter la commande dans le salon de son équipe.

---

## Work Adventures (extensions.workadventures)

- workadventures
  - Usage : `!workadventures`
  - Paramètres : aucun
  - Description : envoie en DM aux membres de la guild leur lien WorkAdventure si connu (utilise un canal `workadventures` comme base de données). Requiert `is_support_user`.

---

## Welcome (extensions.welcome)

- welcome_member
  - Usage : `!welcome_member @membre`
  - Paramètres : membre (discord.Member)
  - Description : applique la logique de bienvenue (naming, rôle) pour le membre indiqué. Utilise les données récupérées depuis l'API (`BOT_URL_API` ➜ `/api/attendees/`) pour retrouver l'entrée correspondante et renommer/attribuer un rôle si nécessaire. (Pas de check de permission explicite dans le code : la commande est exposée.)

- check_attendees
  - Usage : `!check_attendees`
  - Paramètres : aucun
  - Description : parcours les membres du serveur et tente d'appliquer la logique de bienvenue (basée sur les données de l'API). Démarre également périodiquement via une task. Attention : appelle l'API externe.

- change_nicks
  - Usage : `!change_nicks`
  - Paramètres : aucun
  - Description : renomme tous les membres reconnus par l'API selon la convention (Prénom NOMInitiale). Utilise l'API d'attendees pour récupérer les données.

Notes : la cog `WelcomeCog` appelle régulièrement l'API (`BOT_URL_API`) — configurez correctement la variable d'environnement.

---

## Messages automatiques (extensions.auto_message)

Il n'y a pas de commande utilisateur publique, mais cette cog lit un canal configuré (`BOT_CHANNEL_MSG_AUTO`) pour parser des messages planifiés et les publier automatiquement.

---

## Backup / non chargés par défaut

Le dépôt contient aussi `extensions/welcome_bak.py` (version de backup) qui contient des commandes supplémentaires :

- welcome_unknown
  - Usage : `!welcome_unknown`
  - Paramètres : aucun
  - Description : envoie un message DM aux personnes sans rôle pour les inviter à donner leur adresse e-mail. Requiert `is_support_user`.

- users
  - Usage : `!users`
  - Paramètres : aucun
  - Description : affiche le nombre d'utilisateurs par rôle (analyse la base "users" contenue dans un canal). Requiert `is_support_user`.



