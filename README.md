# bot_hic

Un bot discord pour le HIC

## Pré-requis

paquets python à installer (voir `Pipfile`) :

- flask-apscheduler
- discord (py > 1.6.0)
- python-dotenv==0.15.0
- structlog
- requests
- pdfminer.six

## Paramètres d'environnement

Le bot utilise des variables d'environnement pour sa configuration. Voici les variables nécessaires (noms exacts attendus par l'application) :

| Nom (variable d'environnement) | Utilité / où elle est utilisée                                     | Par défaut                                                             |
|--------------------------------|--------------------------------------------------------------------|------------------------------------------------------------------------|
| `BOT_TOKEN`                    | Token du bot Discord (obligatoire)                                 |                                                                        |
| `BOT_PREFIX`                   | Préfixe d'appel du bot                                             | `!`                                                                    |
| `BOT_ADMIN_ROLE`               | Nom du rôle admin utilisé par le bot (self.settings.ADMIN_ROLE)    | `Support`                                                              |
| `BOT_SUPER_COACH_ROLE`         | Nom du rôle "Super Coach"                                          | `SuperCoach`                                                           |
| `BOT_COACH_ROLE`               | Nom du rôle "Coach"                                                | `Coach`                                                                |
| `BOT_FACILITATEUR_ROLE`        | Nom du rôle "Facilitateur"                                         | `Facilitateur`                                                         |
| `BOT_PROJECT_LEAD_ROLE`        | Nom du rôle Chef de projet (utilisé pour les leads d'équipe)       | `Chef de Projet`                                                       |
| `BOT_ORGA_ROLE`                | Nom du rôle organisateur                                           | `Organisation`                                                         |
| `BOT_WELCOME_MODE`             | Mode d'accueil : `open` = accueil automatique activé (vérifie toutes les 5 min et accueille les nouveaux membres) ; `close` = accueil manuel uniquement (via `!welcome_member`) | `close`                                                                |
| `BOT_TEAM_PREFIX`              | Préfixe attendu pour les noms d'équipes                            | `Equipe-`                                                              |
| `BOT_HELP_LINKS`               | Liens d'aide affichés (séparés par des virgules)                   | `HIC,https://www.hackingindustry.camp,Le sparkboard,...                |
| `BOT_CHANNEL_HELP`             | Nom du canal d'aide                                                | `demandes-aide`                                                        |
| `BOT_CHANNEL_SUPPORT`          | Nom du canal de support technique                                  | `support-technique`                                                    |
| `BOT_CHANNEL_WELCOME`          | Nom du canal de bienvenue                                          | `bienvenue`                                                            |
| `BOT_CHANNEL_MSG_AUTO`         | Nom du canal pour messages automatiques                            | `msg_auto`                                                             |
| `BOT_CHANNEL_VOTE`             | Nom du canal de votes                                              | `votes`                                                                |
| `BOT_PARTICIPANT_ROLE`         | Nom du rôle participant                                            | `Participant`                                                          |
| `BOT_TEAM_CATEGORY`            | Nom de la catégorie contenant les salons d'équipes                 | `Participants`                                                         |
| `BOT_JURY_ROLE`                | Nom du rôle jury                                                   | `Jury`                                                                 |
| `BOT_URL_API`                  | URL de l'API externe utilisée par le bot (utilisée par `requests`) | `https://hic-manager-dev.osc-fr1.scalingo.io`                          |
| `SERVER_NAME`                  | Nom du serveur Discord                                             | `Hacking Industry Camp`                                                |
| `SERVER_ID`                    | ID numérique du serveur (utilisé pour retrouver la guild)          | `804784231732740106`                                                   |
| `EVENT_NAME`                   | Nom de l'événement                                                 | `Hacking Industry Camp`                                                |
| `EVENT_CODE`                   | Code interne de l'événement (utilisé pour filtrer équipes)         | `hic-2021`                                                             |
| `EVENT_PLANNING_URL`           | URL vers le PDF du planning (utilisé par la commande `!planning`)  | `https://www.hackingindustry.camp/HIC2022-Planning-Previsionnel.pdf`   |
| `EVENT_ICON_URL`               | URL de l'icône / vignette de l'événement                           | `https://www.hackingindustry.camp/images/logos/Logo_HIC_White.png`     |
| `PDF_DIR`                      | (optionnel) répertoire local contenant des PDF                     |                                                                        |
| `TIMEZONE`                     | Fuseau horaire pour la planification                               |                                                                        |

Remarque : placez ces variables dans un fichier `.env` à la racine du projet ou exportez-les dans l'environnement d'exécution. Gardez `BOT_TOKEN` secret.

## Commandes du bot

Les commandes disponibles sont documentées dans le fichier [BOT_COMMANDS.md](BOT_COMMANDS.md).