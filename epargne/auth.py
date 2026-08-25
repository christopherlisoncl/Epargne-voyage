from functools import wraps

from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from .extensions import db
from .models import Participant, Coach

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


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
