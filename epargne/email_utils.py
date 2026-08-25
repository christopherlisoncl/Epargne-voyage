import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def envoyer_email_bienvenue(app, destinataire: str, nom: str, code: str, url_site: str):
    """Envoie l'email de bienvenue via Gmail SMTP. Retourne (succes, erreur)."""
    adresse = app.config.get("EMAIL_ADRESSE")
    mot_de_passe = app.config.get("EMAIL_MOT_DE_PASSE_APP")

    if not adresse or not mot_de_passe:
        return False, "Email non configuré côté serveur (EMAIL_ADRESSE / EMAIL_MOT_DE_PASSE_APP manquants)."

    msg = MIMEMultipart()
    msg["From"] = adresse
    msg["To"] = destinataire
    msg["Subject"] = "Bienvenue dans la Cagnotte Voyage ! 🌍"

    corps = f"""Bonjour {nom},

Bienvenue dans l'aventure ! Ton espace personnel de suivi d'épargne est prêt.

Pour te connecter :
{url_site}

Ton nom : {nom}
Ton code personnel : {code}

Tu pourras y suivre ta progression mois après mois et prendre rendez-vous avec ton coach.

À bientôt !
"""
    msg.attach(MIMEText(corps, "plain"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as serveur:
            serveur.login(adresse, mot_de_passe)
            serveur.send_message(msg)
        return True, None
    except Exception as e:
        return False, str(e)
