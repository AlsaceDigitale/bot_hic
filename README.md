# bot_hic

Un bot discord pour le HIC2021

## Objectifs

# MUST
- permet de créer des équipes en indiquant les membres et crée un salon pour eux
- permet d'appeler une équipe.
- permet à un participant de ping tous les bénévoles en ligne lorsqu'il a besoin d'aide.
- envoyer des messages pré-programmés sur une liste de channels à heures fixes
  - pouvoir configurer le texte, l'image, le lien
  - pouvoir configurer les channels
  - pouvoir configurer une fréquence de répétition

# MAY
- donne l'agenda sur simple commande
- annonce les évènements de l'agenda sur des channels spécifiés, en donnant le temps restant avant le début
- peut créer un système de vote sondage avec un nombre de votes 
maximum par utilisateur (default 1)

## Pré-requis
paquets python à installer :
- discord
- shlex
- python-dotenv
- pdfminer.six
