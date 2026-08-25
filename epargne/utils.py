import random
import string
from datetime import date

from .models import Participant


def generer_code(longueur: int = 4) -> str:
    return "".join(random.choices(string.digits, k=longueur))


def generer_code_unique(longueur: int = 4, tentatives_max: int = 50) -> str:
    for _ in range(tentatives_max):
        code = generer_code(longueur)
        existe = Participant.query.filter(Participant.code_visible == code).first()
        if not existe:
            return code
    # Filet de sécurité si beaucoup de collisions (peu probable avec ~40 users)
    return generer_code(longueur + 2)


def premier_jour_mois(d: date) -> date:
    return date(d.year, d.month, 1)


def calculer_tableau_mensuel(participant: Participant, aujourdhui: date = None):
    """Construit les lignes du tableau de suivi avec cumul et écart."""
    aujourdhui = aujourdhui or date.today()
    lignes = []
    cumul_realise = 0.0
    cumul_prevu = 0.0
    for m in sorted(participant.mois, key=lambda x: x.mois):
        cumul_prevu += m.epargne_prevue
        cumul_realise += m.epargne_realisee
        ecart = round(cumul_realise - cumul_prevu, 2)
        lignes.append(
            {
                "id": m.id,
                "mois": m.mois,
                "epargne_prevue": m.epargne_prevue,
                "epargne_realisee": m.epargne_realisee,
                "cumul_realise": round(cumul_realise, 2),
                "cumul_prevu": round(cumul_prevu, 2),
                "ecart": ecart,
                "est_mois_courant": premier_jour_mois(aujourdhui) == m.mois,
                "est_futur": m.mois > premier_jour_mois(aujourdhui),
            }
        )
    return lignes


def calculer_statistiques(participant: Participant, aujourdhui: date = None):
    """Calcule progression, écart global et statut du participant."""
    aujourdhui = aujourdhui or date.today()
    mois_courant = premier_jour_mois(aujourdhui)

    cumul_realise_total = sum(m.epargne_realisee for m in participant.mois)
    cumul_prevu_a_ce_jour = sum(
        m.epargne_prevue for m in participant.mois if m.mois <= mois_courant
    )

    ecart = round(cumul_realise_total - cumul_prevu_a_ce_jour, 2)
    mensualite = participant.objectif_total / participant.nb_mois if participant.nb_mois else 1

    if ecart >= -0.5 * mensualite:
        statut = "a_jour"
    elif ecart >= -1.5 * mensualite:
        statut = "a_surveiller"
    else:
        statut = "en_retard"

    pourcentage = 0.0
    if participant.objectif_total:
        pourcentage = round(min(100.0, cumul_realise_total / participant.objectif_total * 100), 1)

    return {
        "cumul_realise_total": round(cumul_realise_total, 2),
        "cumul_prevu_a_ce_jour": round(cumul_prevu_a_ce_jour, 2),
        "ecart": ecart,
        "statut": statut,
        "pourcentage": pourcentage,
    }


STATUT_LABELS = {
    "a_jour": "À jour",
    "a_surveiller": "À surveiller",
    "en_retard": "En retard",
}


def prochain_et_dernier_rdv(participant: Participant, aujourdhui: date = None):
    aujourdhui = aujourdhui or date.today()
    rdvs = sorted(participant.rendezvous, key=lambda r: r.date_rdv)
    passes = [r for r in rdvs if r.date_rdv <= aujourdhui]
    futurs = [r for r in rdvs if r.date_rdv > aujourdhui]
    dernier = passes[-1] if passes else None
    prochain = futurs[0] if futurs else None
    return dernier, prochain
