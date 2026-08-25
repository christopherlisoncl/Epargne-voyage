from functools import wraps

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app

from .extensions import db
from .models import Participant, Coach
from .utils import generer_code_unique
from .email_utils import envoyer_email_bienvenue
from config import Config

auth_bp = Blueprint("auth", __name__)


def participant_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("role") != "participant":
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped


def coach_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("role") != "coach":
            return redirect(url_for("auth.coach_login"))
        return view(*args, **kwargs)

    return wrapped


@auth_bp.route("/", methods=["GET", "POST"])
def login():
    participants = Participant.query.order_by(Participant.nom).all()

    if request.method == "POST":
        participant_id = request.form.get("participant_id", type=int)
        code = request.form.get("code", "").strip()

        participant = Participant.query.get(participant_id) if participant_id else None
        if participant and participant.check_code(code):
            session.clear()
            session["role"] = "participant"
            session["user_id"] = participant.id
            return redirect(url_for("participant.dashboard"))

        flash("Nom ou code incorrect. Vérifie auprès de ton coach si besoin.", "error")

    return render_template("login.html", participants=participants)


@auth_bp.route("/coach/login", methods=["GET", "POST"])
def coach_login():
    if request.method == "POST":
        code = request.form.get("code", "").strip()
        coach = Coach.query.first()
        if coach and coach.check_code(code):
            session.clear()
            session["role"] = "coach"
            session["user_id"] = coach.id
            return redirect(url_for("coach.overview"))
        flash("Code coach incorrect.", "error")

    return render_template("coach_login.html")


@auth_bp.route("/inscription", methods=["GET", "POST"])
def inscription():
    if request.method == "POST":
        nom = request.form.get("nom", "").strip()
        email = request.form.get("email", "").strip()

        if not nom:
            flash("Le nom est obligatoire.", "error")
            return redirect(url_for("auth.inscription"))

        participant = Participant(
            nom=nom,
            objectif_total=Config.OBJECTIF_DEFAUT,
            date_debut=Config.DATE_DEBUT_DEFAUT,
            nb_mois=Config.NB_MOIS_DEFAUT,
        )
        code = generer_code_unique()
        participant.set_code(code)
        db.session.add(participant)
        db.session.flush()
        participant.generer_plan_mensuel()
        db.session.commit()

        url_site = url_for("auth.login", _external=True)
        email_envoye = False
        if email:
            email_envoye, erreur = envoyer_email_bienvenue(current_app, email, nom, code, url_site)

        return render_template(
            "inscription_confirmation.html",
            nom=nom,
            code=code,
            email=email,
            email_envoye=email_envoye,
        )

    return render_template("inscription.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
