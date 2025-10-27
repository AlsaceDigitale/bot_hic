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

Le bot utilise des variables d'environnement pour sa configuration. Voici les variables nécessaires :

| Nom              | Utilité                                     | Exemple                       |
|------------------|---------------------------------------------|-------------------------------|
| `BOT_TOKEN`      | Token du bot Discord (obligatoire)          | N/A (secret)                  |
| `BOT_PREFIX`     | Préfixe d'appel du bot                      | `!`                           |
| `SERVER_NAME`    | Nom du serveur Discord                      | `Hacking Industry Camp`       |
| `SERVER_ID`      | ID numérique du serveur (alternative utile) | `123456789012345678`          |
| `EVENT_NAME`     | Nom de l'événement                          | `Hacking Industry Camp`       |
| `EVENT_DATE`     | Date de l'événement (utilisé par les commandes de planning) | `2025-08-01`                  |
| `ADMIN_ROLE`     | Nom ou ID du rôle disposant des droits admin | `Organisateur` ou `987654321` |
| `OWNER_ID`       | ID Discord du propriétaire du bot           | `123456789012345678`          |
| `LOG_CHANNEL_ID` | Channel ID pour les logs / notifications    | `234567890123456789`          |
| `PDF_DIR`        | Répertoire contenant les PDF (pdfminer)     | `./data/pdfs`                 |
| `TIMEZONE`       | Fuseau horaire pour la planification        | `Europe/Paris`                |

Remarque : placez ces variables dans un fichier `.env` à la racine du projet ou exportez-les dans l'environnement 
d'exécution. Gardez `BOT_TOKEN` secret.
