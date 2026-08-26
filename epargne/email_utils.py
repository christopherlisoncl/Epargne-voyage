import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def _envoyer(app, destinataire: str, sujet: str, corps: str):
    adresse = app.config.get("EMAIL_ADRESSE")
    mot_de_passe = app.config.get("EMAIL_MOT_DE_PASSE_APP")

    if not adresse or not mot_de_passe:
        return False, "Email non configuré côté serveur (EMAIL_ADRESSE / EMAIL_MOT_DE_PASSE_APP manquants)."

    msg = MIMEMultipart()
    msg["From"] = adresse
    msg["To"] = destinataire
    msg["Subject"] = sujet
    msg.attach(MIMEText(corps, "plain"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as serveur:
            serveur.login(adresse, mot_de_passe)
            serveur.send_message(msg)
        return True, None
    except Exception as e:
        return False, str(e)


def envoyer_email_bienvenue(app, destinataire: str, nom: str, code: str, url_site: str):
    """Envoie l'email de bienvenue via Gmail SMTP. Retourne (succes, erreur)."""
    corps = f"""Bonjour {nom},

Bienvenue dans l'aventure ! Ton espace personnel de suivi d'épargne est prêt.

Pour te connecter :
{url_site}

Ton nom : {nom}
Ton code personnel : {code}

Tu pourras y suivre ta progression mois après mois et prendre rendez-vous avec ton coach.

À bientôt !
"""
    return _envoyer(app, destinataire, "Bienvenue dans la Cagnotte Voyage ! 🌍", corps)


def envoyer_email_code_oublie(app, destinataire: str, nom: str, code: str, url_site: str):
    """Envoie un rappel du code d'accès via Gmail SMTP. Retourne (succes, erreur)."""
    corps = f"""Bonjour {nom},

Voici ton code d'accès à la Cagnotte Voyage, comme demandé :

Ton nom : {nom}
Ton code personnel : {code}

Connecte-toi ici : {url_site}

Si tu n'es pas à l'origine de cette demande, tu peux ignorer cet email.
"""
    return _envoyer(app, destinataire, "Ton code d'accès — Cagnotte Voyage", corps)
