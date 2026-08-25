# Cagnotte Voyage 🌍

Application web de suivi d'épargne collective pour un groupe qui économise en vue d'un voyage.
Chaque participant déclare mensuellement ce qu'il a épargné ; le coach a une vue d'ensemble et suit
chacun en 1-to-1.

## Stack technique

- **Backend** : Python 3 / Flask
- **Base de données** : SQLite (via Flask-SQLAlchemy) — largement suffisant pour 15–40 utilisateurs
- **Frontend** : templates Jinja2 + CSS simple (pas de framework JS) — fonctionne sans JavaScript
- Aucune dépendance à Node.js

## Modèle de données

- **Coach** : nom + code d'accès (un seul coach pour l'instant)
- **Participant** : nom, code d'accès, objectif total (2000 € par défaut), date de début, nombre de mois (12 par défaut)
- **MoisEpargne** : une ligne par participant et par mois, avec épargne prévue et épargne réalisée
- **RendezVous** : date + notes, un participant peut en avoir plusieurs (passés et futurs)

Le statut (**À jour / À surveiller / En retard**) et le pourcentage de progression sont **calculés à la volée**
(jamais stockés) à partir de l'écart entre le cumul réalisé et le cumul prévu à la date du jour. Voir
[`epargne/utils.py`](epargne/utils.py) pour la logique exacte (le seuil se base sur la mensualité :
À jour si l'écart est ≥ -0,5 mensualité, À surveiller jusqu'à -1,5 mensualité, En retard au-delà).

## Lancer le projet en local

```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
cp .env.example .env   # puis modifie SECRET_KEY et COACH_CODE_DEFAUT
```

Initialiser la base de données (crée les tables + le compte coach) :

```bash
FLASK_APP=wsgi:app ./venv/bin/flask init-db
```

Lancer le serveur de développement :

```bash
./venv/bin/python run.py
```

L'application est disponible sur http://127.0.0.1:5000. Le code coach par défaut est celui défini dans
`.env` (`COACH_CODE_DEFAUT`).

## Ajouter les participants

Une fois connecté en tant que coach : **Vue d'ensemble → + Ajouter un participant**. Un code à 4 chiffres
est généré automatiquement et affiché — c'est ce code (avec le nom) que le participant utilisera pour se
connecter. Le coach peut le retrouver ou le régénérer à tout moment depuis la fiche du participant.

## Déploiement

Voir la section dédiée ci-dessous / demande à Claude de t'accompagner pas à pas.
