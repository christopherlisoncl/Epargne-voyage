from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from .auth import participant_required
from .extensions import db
from .models import Participant, MoisEpargne, Coach
from .utils import (
    calculer_tableau_mensuel,
    calculer_statistiques,
    prochain_et_dernier_rdv,
    generer_svg_progression,
    STATUT_LABELS,
)

participant_bp = Blueprint("participant", __name__, url_prefix="/espace")


def _current_participant():
    return Participant.query.get(session["user_id"])


@participant_bp.route("/")
@participant_required
def dashboard():
    participant = _current_participant()
    if not participant:
        session.clear()
        return redirect(url_for("auth.login"))

    lignes = calculer_tableau_mensuel(participant)
    stats = calculer_statistiques(participant)
    dernier_rdv, prochain_rdv = prochain_et_dernier_rdv(participant)
    coach = Coach.query.first()
    svg_progression = generer_svg_progression(lignes, participant.objectif_total)

    return render_template(
        "participant/dashboard.html",
        participant=participant,
        lignes=lignes,
        stats=stats,
        statut_label=STATUT_LABELS[stats["statut"]],
        dernier_rdv=dernier_rdv,
        prochain_rdv=prochain_rdv,
        coach=coach,
        svg_progression=svg_progression,
    )


@participant_bp.route("/enregistrer", methods=["POST"])
@participant_required
def enregistrer():
    participant = _current_participant()
    if not participant:
        session.clear()
        return redirect(url_for("auth.login"))

    for mois in participant.mois:
        champ = f"montant_{mois.id}"
        if champ in request.form:
            valeur = request.form.get(champ, "").strip().replace(",", ".")
            try:
                mois.epargne_realisee = max(0.0, float(valeur)) if valeur else 0.0
            except ValueError:
                continue

    db.session.commit()
    flash("Tes montants ont bien été enregistrés. Bravo pour ta régularité !", "success")
    return redirect(url_for("participant.dashboard"))
