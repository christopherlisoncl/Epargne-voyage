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


def generer_svg_progression(lignes, objectif_total, largeur=600, hauteur=220):
    """Génère un petit graphique SVG (cumul prévu vs réalisé) à partir des lignes
    calculées par calculer_tableau_mensuel."""
    if not lignes:
        return ""

    marge_g, marge_d, marge_h, marge_b = 36, 12, 16, 30
    n = len(lignes)
    max_val = max(
        [objectif_total] + [l["cumul_prevu"] for l in lignes] + [l["cumul_realise"] for l in lignes]
    ) or 1

    def pos_x(i):
        if n == 1:
            return marge_g
        return marge_g + i * (largeur - marge_g - marge_d) / (n - 1)

    def pos_y(val):
        return hauteur - marge_b - (val / max_val) * (hauteur - marge_h - marge_b)

    pts_prevu = " ".join(f"{pos_x(i):.1f},{pos_y(l['cumul_prevu']):.1f}" for i, l in enumerate(lignes))
    pts_realise = " ".join(f"{pos_x(i):.1f},{pos_y(l['cumul_realise']):.1f}" for i, l in enumerate(lignes))

    # Étiquettes de mois (une sur deux si trop nombreuses, pour ne pas surcharger)
    pas_etiquette = 2 if n > 8 else 1
    etiquettes = ""
    noms_mois = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"]
    for i, l in enumerate(lignes):
        if i % pas_etiquette == 0:
            etiquettes += (
                f'<text x="{pos_x(i):.1f}" y="{hauteur - 8}" font-size="10" fill="#83766a" '
                f'text-anchor="middle">{noms_mois[l["mois"].month - 1]}</text>'
            )

    dernier_point_x = pos_x(n - 1)
    dernier_point_y = pos_y(lignes[-1]["cumul_realise"])

    return f'''<svg viewBox="0 0 {largeur} {hauteur}" xmlns="http://www.w3.org/2000/svg" style="width:100%; height:auto; display:block;">
  <line x1="{marge_g}" y1="{hauteur - marge_b}" x2="{largeur - marge_d}" y2="{hauteur - marge_b}" stroke="#e6dccb" stroke-width="1"/>
  <polyline points="{pts_prevu}" fill="none" stroke="#83766a" stroke-width="2" stroke-dasharray="5,5" opacity="0.7"/>
  <polyline points="{pts_realise}" fill="none" stroke="#e07a5f" stroke-width="3"/>
  <circle cx="{dernier_point_x:.1f}" cy="{dernier_point_y:.1f}" r="4.5" fill="#e07a5f"/>
  {etiquettes}
</svg>'''


def prochain_et_dernier_rdv(participant: Participant, aujourdhui: date = None):
    aujourdhui = aujourdhui or date.today()
    rdvs = sorted(participant.rendezvous, key=lambda r: r.date_rdv)
    passes = [r for r in rdvs if r.date_rdv <= aujourdhui]
    futurs = [r for r in rdvs if r.date_rdv > aujourdhui]
    dernier = passes[-1] if passes else None
    prochain = futurs[0] if futurs else None
    return dernier, prochain
