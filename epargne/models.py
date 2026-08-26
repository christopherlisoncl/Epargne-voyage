from datetime import datetime, date

from werkzeug.security import generate_password_hash, check_password_hash

from .extensions import db


def add_months(d: date, n: int) -> date:
    """Retourne le 1er jour du mois n mois après d."""
    month_index = d.month - 1 + n
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    return date(year, month, 1)


class Coach(db.Model):
    __tablename__ = "coach"

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(80), nullable=False)
    code_hash = db.Column(db.String(255), nullable=False)
    # Conservé en clair pour permettre au coach de le retrouver/partager
    # (outil déclaratif à faible enjeu, pas de données bancaires).
    code_visible = db.Column(db.String(6), nullable=False)

    email = db.Column(db.String(255), nullable=True)
    telephone = db.Column(db.String(50), nullable=True)
    lien_rdv = db.Column(db.String(500), nullable=True)
    date_voyage = db.Column(db.Date, nullable=True)

    def set_code(self, code: str):
        self.code_visible = code
        self.code_hash = generate_password_hash(code, method="pbkdf2:sha256")

    def check_code(self, code: str) -> bool:
        return check_password_hash(self.code_hash, code)


class Participant(db.Model):
    __tablename__ = "participant"

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(120), nullable=False)
    code_hash = db.Column(db.String(255), nullable=False)
    code_visible = db.Column(db.String(6), nullable=False)
    email = db.Column(db.String(255), nullable=True)

    objectif_total = db.Column(db.Float, nullable=False, default=2000.0)
    date_debut = db.Column(db.Date, nullable=False)
    nb_mois = db.Column(db.Integer, nullable=False, default=12)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    mois = db.relationship(
        "MoisEpargne",
        backref="participant",
        cascade="all, delete-orphan",
        order_by="MoisEpargne.mois",
    )
    rendezvous = db.relationship(
        "RendezVous",
        backref="participant",
        cascade="all, delete-orphan",
        order_by="RendezVous.date_rdv",
    )

    def set_code(self, code: str):
        self.code_visible = code
        self.code_hash = generate_password_hash(code, method="pbkdf2:sha256")

    def check_code(self, code: str) -> bool:
        return check_password_hash(self.code_hash, code)

    def generer_plan_mensuel(self):
        """(Re)génère les lignes mensuelles avec une épargne prévue répartie
        uniformément sur la durée du projet, en conservant les montants déjà
        déclarés par le participant."""
        montant_mensuel = round(self.objectif_total / self.nb_mois, 2)
        existants = {m.mois: m for m in self.mois}

        for i in range(self.nb_mois):
            mois_date = add_months(self.date_debut, i)
            if mois_date in existants:
                existants[mois_date].epargne_prevue = montant_mensuel
            else:
                db.session.add(
                    MoisEpargne(
                        participant_id=self.id,
                        mois=mois_date,
                        epargne_prevue=montant_mensuel,
                        epargne_realisee=0.0,
                    )
                )


class MoisEpargne(db.Model):
    __tablename__ = "mois_epargne"
    __table_args__ = (db.UniqueConstraint("participant_id", "mois"),)

    id = db.Column(db.Integer, primary_key=True)
    participant_id = db.Column(db.Integer, db.ForeignKey("participant.id"), nullable=False)
    mois = db.Column(db.Date, nullable=False)
    epargne_prevue = db.Column(db.Float, nullable=False, default=0.0)
    epargne_realisee = db.Column(db.Float, nullable=False, default=0.0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class RendezVous(db.Model):
    __tablename__ = "rendez_vous"

    id = db.Column(db.Integer, primary_key=True)
    participant_id = db.Column(db.Integer, db.ForeignKey("participant.id"), nullable=False)
    date_rdv = db.Column(db.Date, nullable=False)
    notes = db.Column(db.Text, nullable=True, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
