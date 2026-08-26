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


COULEURS_STATUT = {
    "a_jour": "#6a9c78",
    "a_surveiller": "#d8952c",
    "en_retard": "#c4553e",
}


def generer_jauge_circulaire(pourcentage, statut=None, taille=200):
    """Génère une jauge circulaire SVG (anneau qui se remplit selon le pourcentage)."""
    pourcentage = max(0.0, min(100.0, pourcentage))
    couleur = COULEURS_STATUT.get(statut, "#e07a5f")
    rayon = taille / 2 - 18
    centre = taille / 2
    circonference = 2 * 3.14159265 * rayon
    decalage = circonference * (1 - pourcentage / 100)

    return f'''<svg viewBox="0 0 {taille} {taille}" xmlns="http://www.w3.org/2000/svg" style="width:100%; max-width:220px; height:auto; display:block; margin:0 auto;">
  <circle cx="{centre}" cy="{centre}" r="{rayon}" fill="none" stroke="#f3e4d0" stroke-width="16"/>
  <circle cx="{centre}" cy="{centre}" r="{rayon}" fill="none" stroke="{couleur}" stroke-width="16"
          stroke-linecap="round" stroke-dasharray="{circonference:.1f}" stroke-dashoffset="{decalage:.1f}"
          transform="rotate(-90 {centre} {centre})" style="transition: stroke-dashoffset 0.4s ease;"/>
  <text x="{centre}" y="{centre - 4}" text-anchor="middle" font-size="34" font-weight="800" fill="#3a3128" font-family="inherit">{pourcentage:.0f}%</text>
  <text x="{centre}" y="{centre + 20}" text-anchor="middle" font-size="12" fill="#83766a" font-family="inherit">épargné</text>
</svg>'''


def prochain_et_dernier_rdv(participant: Participant, aujourdhui: date = None):
    aujourdhui = aujourdhui or date.today()
    rdvs = sorted(participant.rendezvous, key=lambda r: r.date_rdv)
    passes = [r for r in rdvs if r.date_rdv <= aujourdhui]
    futurs = [r for r in rdvs if r.date_rdv > aujourdhui]
    dernier = passes[-1] if passes else None
    prochain = futurs[0] if futurs else None
    return dernier, prochain


def calculer_serie_a_jour(lignes, aujourdhui: date = None) -> int:
    """Nombre de mois consécutifs (jusqu'au mois courant inclus) où le cumul réalisé
    a couvert le cumul prévu — pour le badge de régularité."""
    aujourdhui = aujourdhui or date.today()
    mois_courant = premier_jour_mois(aujourdhui)
    lignes_passees = [l for l in lignes if l["mois"] <= mois_courant]

    serie = 0
    for ligne in reversed(lignes_passees):
        if ligne["ecart"] >= 0:
            serie += 1
        else:
            break
    return serie


def jours_avant_voyage(date_voyage: date, aujourdhui: date = None):
    """Nombre de jours restants avant le voyage, ou None si pas de date définie
    ou si le voyage est déjà passé."""
    if not date_voyage:
        return None
    aujourdhui = aujourdhui or date.today()
    delta = (date_voyage - aujourdhui).days
    return delta if delta >= 0 else None
