import os
from datetime import date

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-moi-en-production")
    # IMPORTANT : toujours un chemin ABSOLU (sqlite:////...). Flask-SQLAlchemy
    # préfixe automatiquement tout chemin sqlite RELATIF avec app.instance_path
    # (qui vaut déjà .../instance) — un DATABASE_URL du type
    # "sqlite:///instance/epargne.db" donnerait donc .../instance/instance/epargne.db
    # (dossier inexistant -> "unable to open database file").
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'epargne.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Paramètres par défaut du projet d'épargne
    OBJECTIF_DEFAUT = 2000.0
    NB_MOIS_DEFAUT = 12
    DATE_DEBUT_DEFAUT = date(2026, 9, 1)

    # Nom du coach par défaut créé au premier lancement (flask init-db)
    COACH_NOM_DEFAUT = os.environ.get("COACH_NOM_DEFAUT", "Coach")
    COACH_CODE_DEFAUT = os.environ.get("COACH_CODE_DEFAUT", "000000")

    # Envoi d'email de bienvenue via Gmail (mot de passe d'application, pas le mot de passe du compte)
    EMAIL_ADRESSE = os.environ.get("EMAIL_ADRESSE", "")
    EMAIL_MOT_DE_PASSE_APP = os.environ.get("EMAIL_MOT_DE_PASSE_APP", "")
