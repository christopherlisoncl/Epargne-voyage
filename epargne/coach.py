import csv
import io
from datetime import datetime, date, timedelta

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, Response

from .auth import coach_required
from .extensions import db
from .models import Participant, RendezVous, Coach, MoisEpargne
from .utils import (
    calculer_tableau_mensuel,
    calculer_statistiques,
    prochain_et_dernier_rdv,
    generer_code_unique,
    STATUT_LABELS,
)
from config import Config

coach_bp = Blueprint("coach", __name__, url_prefix="/coach")


@coach_bp.route("/profil", methods=["GET", "POST"])
@coach_required
def profil():
    coach = Coach.query.get(session["user_id"])

    if request.method == "POST":
        coach.email = request.form.get("email", "").strip()
        coach.telephone = request.form.get("telephone", "").strip()
        coach.lien_rdv = request.form.get("lien_rdv", "").strip()
        db.session.commit()
        flash("Ton profil a été mis à jour.", "success")
        return redirect(url_for("coach.profil"))

    return render_template("coach/profil.html", coach=coach)


@coach_bp.route("/")
@coach_required
def overview():
    participants = Participant.query.order_by(Participant.nom).all()

    lignes = []
    compteurs = {"a_jour": 0, "a_surveiller": 0, "en_retard": 0}
    somme_pourcentages = 0.0

    for p in participants:
        stats = calculer_statistiques(p)
        dernier_rdv, prochain_rdv = prochain_et_dernier_rdv(p)
        compteurs[stats["statut"]] += 1
        somme_pourcentages += stats["pourcentage"]
        lignes.append(
            {
                "participant": p,
                "stats": stats,
                "statut_label": STATUT_LABELS[stats["statut"]],
                "dernier_rdv": dernier_rdv,
                "prochain_rdv": prochain_rdv,
            }
        )

    progression_moyenne = round(somme_pourcentages / len(participants), 1) if participants else 0.0

    aujourdhui = date.today()
    dans_une_semaine = aujourdhui + timedelta(days=7)
    rdvs_semaine = []
    for p in participants:
        for r in p.rendezvous:
            if aujourdhui <= r.date_rdv <= dans_une_semaine:
                rdvs_semaine.append({"participant": p, "rdv": r})
    rdvs_semaine.sort(key=lambda x: x["rdv"].date_rdv)

    return render_template(
        "coach/dashboard.html",
        lignes=lignes,
        compteurs=compteurs,
        progression_moyenne=progression_moyenne,
        total_participants=len(participants),
        rdvs_semaine=rdvs_semaine,
    )


@coach_bp.route("/export.csv")
@coach_required
def export_csv():
    participants = Participant.query.order_by(Participant.nom).all()
    output = io.StringIO()
    output.write("﻿")  # BOM pour un affichage correct des accents dans Excel
    writer = csv.writer(output)
    writer.writerow(
        ["Nom", "Objectif (€)", "Cumul réalisé (€)", "% objectif", "Statut", "Dernier RDV", "Prochain RDV"]
    )
    for p in participants:
        stats = calculer_statistiques(p)
        dernier_rdv, prochain_rdv = prochain_et_dernier_rdv(p)
        writer.writerow(
            [
                p.nom,
                p.objectif_total,
                stats["cumul_realise_total"],
                stats["pourcentage"],
                STATUT_LABELS[stats["statut"]],
                dernier_rdv.date_rdv.strftime("%d/%m/%Y") if dernier_rdv else "",
                prochain_rdv.date_rdv.strftime("%d/%m/%Y") if prochain_rdv else "",
            ]
        )

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=cagnotte_voyage_export.csv"},
    )


@coach_bp.route("/participant/<int:participant_id>")
@coach_required
def detail(participant_id):
    participant = Participant.query.get_or_404(participant_id)
    lignes = calculer_tableau_mensuel(participant)
    stats = calculer_statistiques(participant)
    dernier_rdv, prochain_rdv = prochain_et_dernier_rdv(participant)
    rendezvous = sorted(participant.rendezvous, key=lambda r: r.date_rdv, reverse=True)

    return render_template(
        "coach/participant_detail.html",
        participant=participant,
        lignes=lignes,
        stats=stats,
        statut_label=STATUT_LABELS[stats["statut"]],
        dernier_rdv=dernier_rdv,
        prochain_rdv=prochain_rdv,
        rendezvous=rendezvous,
        today=date.today(),
    )


@coach_bp.route("/participant/<int:participant_id>/montants", methods=["POST"])
@coach_required
def maj_montants(participant_id):
    participant = Participant.query.get_or_404(participant_id)

    for mois in participant.mois:
        champ_realise = f"realise_{mois.id}"
        champ_prevu = f"prevu_{mois.id}"
        if champ_realise in request.form:
            valeur = request.form.get(champ_realise, "").strip().replace(",", ".")
            try:
                mois.epargne_realisee = max(0.0, float(valeur)) if valeur else 0.0
            except ValueError:
                pass
        if champ_prevu in request.form:
            valeur = request.form.get(champ_prevu, "").strip().replace(",", ".")
            try:
                mois.epargne_prevue = max(0.0, float(valeur)) if valeur else 0.0
            except ValueError:
                pass

    db.session.commit()
    flash(f"Montants de {participant.nom} mis à jour.", "success")
    return redirect(url_for("coach.detail", participant_id=participant.id))


@coach_bp.route("/participant/<int:participant_id>/objectif", methods=["POST"])
@coach_required
def maj_objectif(participant_id):
    participant = Participant.query.get_or_404(participant_id)
    nouvel_objectif = request.form.get("objectif_total", "").strip().replace(",", ".")
    date_debut_str = request.form.get("date_debut", "").strip()

    try:
        participant.objectif_total = max(1.0, float(nouvel_objectif))
    except ValueError:
        flash("Montant d'objectif invalide.", "error")
        return redirect(url_for("coach.detail", participant_id=participant.id))

    if date_debut_str:
        try:
            nouvelle_date = datetime.strptime(date_debut_str, "%Y-%m-%d").date()
        except ValueError:
            flash("Date de début invalide.", "error")
            return redirect(url_for("coach.detail", participant_id=participant.id))

        if nouvelle_date != participant.date_debut:
            # Le mapping mois <-> ligne change entièrement : on repart d'un plan vierge
            # (les montants déjà déclarés sur l'ancien calendrier ne peuvent pas être reportés).
            participant.date_debut = nouvelle_date
            MoisEpargne.query.filter_by(participant_id=participant.id).delete()

    participant.generer_plan_mensuel()
    db.session.commit()
    flash(f"Plan de {participant.nom} mis à jour.", "success")

    return redirect(url_for("coach.detail", participant_id=participant.id))


@coach_bp.route("/participant/<int:participant_id>/rdv/nouveau", methods=["POST"])
@coach_required
def ajouter_rdv(participant_id):
    participant = Participant.query.get_or_404(participant_id)
    date_str = request.form.get("date_rdv", "").strip()
    notes = request.form.get("notes", "").strip()

    try:
        date_rdv = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        flash("Date de rendez-vous invalide.", "error")
        return redirect(url_for("coach.detail", participant_id=participant.id))

    rdv = RendezVous(participant_id=participant.id, date_rdv=date_rdv, notes=notes)
    db.session.add(rdv)
    db.session.commit()
    flash("Rendez-vous ajouté.", "success")
    return redirect(url_for("coach.detail", participant_id=participant.id))


@coach_bp.route("/participant/<int:participant_id>/rdv/<int:rdv_id>/modifier", methods=["POST"])
@coach_required
def modifier_rdv(participant_id, rdv_id):
    rdv = RendezVous.query.filter_by(id=rdv_id, participant_id=participant_id).first_or_404()
    date_str = request.form.get("date_rdv", "").strip()
    notes = request.form.get("notes", "").strip()

    try:
        rdv.date_rdv = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        flash("Date de rendez-vous invalide.", "error")
        return redirect(url_for("coach.detail", participant_id=participant_id))

    rdv.notes = notes
    db.session.commit()
    flash("Rendez-vous mis à jour.", "success")
    return redirect(url_for("coach.detail", participant_id=participant_id))


@coach_bp.route("/participant/<int:participant_id>/rdv/<int:rdv_id>/supprimer", methods=["POST"])
@coach_required
def supprimer_rdv(participant_id, rdv_id):
    rdv = RendezVous.query.filter_by(id=rdv_id, participant_id=participant_id).first_or_404()
    db.session.delete(rdv)
    db.session.commit()
    flash("Rendez-vous supprimé.", "success")
    return redirect(url_for("coach.detail", participant_id=participant_id))


@coach_bp.route("/participant/<int:participant_id>/renommer", methods=["POST"])
@coach_required
def renommer_participant(participant_id):
    participant = Participant.query.get_or_404(participant_id)
    nouveau_nom = request.form.get("nom", "").strip()
    if nouveau_nom:
        participant.nom = nouveau_nom
        db.session.commit()
        flash("Nom mis à jour.", "success")
    else:
        flash("Le nom ne peut pas être vide.", "error")
    return redirect(url_for("coach.detail", participant_id=participant.id))


@coach_bp.route("/participant/<int:participant_id>/supprimer", methods=["POST"])
@coach_required
def supprimer_participant(participant_id):
    participant = Participant.query.get_or_404(participant_id)
    nom = participant.nom
    db.session.delete(participant)
    db.session.commit()
    flash(f"{nom} a été retiré·e du suivi.", "success")
    return redirect(url_for("coach.overview"))


@coach_bp.route("/participant/<int:participant_id>/regenerer-code", methods=["POST"])
@coach_required
def regenerer_code(participant_id):
    participant = Participant.query.get_or_404(participant_id)
    nouveau_code = generer_code_unique()
    participant.set_code(nouveau_code)
    db.session.commit()
    flash(f"Nouveau code généré pour {participant.nom} : {nouveau_code}", "success")
    return redirect(url_for("coach.detail", participant_id=participant.id))


@coach_bp.route("/nouveau", methods=["GET", "POST"])
@coach_required
def nouveau_participant():
    if request.method == "POST":
        nom = request.form.get("nom", "").strip()
        objectif = request.form.get("objectif_total", "").strip().replace(",", ".")
        date_debut_str = request.form.get("date_debut", "").strip()

        if not nom:
            flash("Le nom est obligatoire.", "error")
            return redirect(url_for("coach.nouveau_participant"))

        try:
            objectif_total = float(objectif) if objectif else Config.OBJECTIF_DEFAUT
        except ValueError:
            objectif_total = Config.OBJECTIF_DEFAUT

        try:
            date_debut = (
                datetime.strptime(date_debut_str, "%Y-%m-%d").date()
                if date_debut_str
                else Config.DATE_DEBUT_DEFAUT
            )
        except ValueError:
            date_debut = Config.DATE_DEBUT_DEFAUT

        participant = Participant(
            nom=nom,
            objectif_total=objectif_total,
            date_debut=date_debut,
            nb_mois=Config.NB_MOIS_DEFAUT,
        )
        code = generer_code_unique()
        participant.set_code(code)
        db.session.add(participant)
        db.session.flush()  # pour obtenir participant.id avant de générer le plan
        participant.generer_plan_mensuel()
        db.session.commit()

        flash(f"{nom} a été ajouté·e. Code d'accès : {code}", "success")
        return redirect(url_for("coach.detail", participant_id=participant.id))

    return render_template("coach/nouveau_participant.html", objectif_defaut=Config.OBJECTIF_DEFAUT,
                            date_debut_defaut=Config.DATE_DEBUT_DEFAUT)
