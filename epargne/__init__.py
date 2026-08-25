import os

import click
from flask import Flask

from .extensions import db


def create_app(config_object="config.Config"):
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(config_object)

    os.makedirs(os.path.join(app.root_path, "..", "instance"), exist_ok=True)

    db.init_app(app)

    from .auth import auth_bp
    from .participant import participant_bp
    from .coach import coach_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(participant_bp)
    app.register_blueprint(coach_bp)

    register_cli(app)
    register_template_filters(app)

    return app


def register_cli(app):
    @app.cli.command("init-db")
    def init_db_command():
        """Crée les tables et un coach par défaut si aucun n'existe."""
        from .models import Coach

        with app.app_context():
            db.create_all()
            if not Coach.query.first():
                coach = Coach(nom=app.config["COACH_NOM_DEFAUT"])
                coach.set_code(app.config["COACH_CODE_DEFAUT"])
                db.session.add(coach)
                db.session.commit()
                click.echo(
                    f"Coach créé : {coach.nom} — code d'accès : {app.config['COACH_CODE_DEFAUT']}"
                )
            else:
                click.echo("Base déjà initialisée.")

    @app.cli.command("migrate-db")
    def migrate_db_command():
        """Ajoute les colonnes manquantes aux tables existantes, sans perte de données."""
        from sqlalchemy import inspect, text

        with app.app_context():
            inspector = inspect(db.engine)
            existing_cols = {c["name"] for c in inspector.get_columns("coach")}
            colonnes_attendues = {
                "email": "VARCHAR(255)",
                "telephone": "VARCHAR(50)",
                "lien_rdv": "VARCHAR(500)",
            }
            a_ajouter = {
                nom: type_sql
                for nom, type_sql in colonnes_attendues.items()
                if nom not in existing_cols
            }
            if not a_ajouter:
                click.echo("Rien à migrer, la base est déjà à jour.")
                return
            with db.engine.begin() as conn:
                for nom, type_sql in a_ajouter.items():
                    conn.execute(text(f"ALTER TABLE coach ADD COLUMN {nom} {type_sql}"))
            click.echo(f"{len(a_ajouter)} colonne(s) ajoutée(s) : {', '.join(a_ajouter)}")


def register_template_filters(app):
    @app.template_filter("euros")
    def euros(value):
        try:
            return f"{value:,.0f} €".replace(",", " ")
        except (TypeError, ValueError):
            return value

    @app.template_filter("mois_fr")
    def mois_fr(d):
        noms = [
            "janvier", "février", "mars", "avril", "mai", "juin",
            "juillet", "août", "septembre", "octobre", "novembre", "décembre",
        ]
        if not d:
            return ""
        return f"{noms[d.month - 1]} {d.year}"

    @app.template_filter("date_fr")
    def date_fr(d):
        if not d:
            return ""
        return d.strftime("%d/%m/%Y")
