import os
from datetime import date

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-moi-en-production")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'epargne.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Paramètres par défaut du projet d'épargne
    OBJECTIF_DEFAUT = 2000.0
    NB_MOIS_DEFAUT = 12
    DATE_DEBUT_DEFAUT = date(2025, 9, 1)

    # Nom du coach par défaut créé au premier lancement (flask init-db)
    COACH_NOM_DEFAUT = os.environ.get("COACH_NOM_DEFAUT", "Coach")
    COACH_CODE_DEFAUT = os.environ.get("COACH_CODE_DEFAUT", "000000")
