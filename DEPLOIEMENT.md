# Déploiement sur PythonAnywhere (gratuit)

Guide pas à pas pour mettre Cagnotte Voyage en ligne gratuitement, avec une base SQLite persistante.

## A. Pousser le code sur GitHub (en local, sur ton ordinateur)

1. Va sur https://github.com/new et crée un dépôt (par exemple `epargne-voyage`).
   Recommandé : coche **Private**. Ne coche pas "Add a README" (on en a déjà un).
2. Dans le terminal, à la racine du projet :

```bash
git remote add origin https://github.com/TON_PSEUDO/epargne-voyage.git
git branch -M main
git push -u origin main
```

Remplace `TON_PSEUDO` par ton nom d'utilisateur GitHub. Si GitHub te demande un mot de passe lors du
`push`, utilise un **Personal Access Token** (Settings → Developer settings → Personal access tokens sur
GitHub) à la place du mot de passe — GitHub n'accepte plus les mots de passe classiques en ligne de commande.

## B. Créer un compte PythonAnywhere

Va sur https://www.pythonanywhere.com/registration/register/beginner/ et crée un compte gratuit
("Beginner account").

## C. Récupérer le code sur PythonAnywhere

Dans le dashboard PythonAnywhere : onglet **Consoles** → **Bash**. Dans la console qui s'ouvre :

```bash
git clone https://github.com/TON_PSEUDO/epargne-voyage.git
cd epargne-voyage
```

Si le dépôt est privé, Git te demandera ton nom d'utilisateur GitHub puis, comme mot de passe, le même
Personal Access Token que ci-dessus.

## D. Créer l'environnement virtuel et installer les dépendances

Toujours dans la console Bash PythonAnywhere :

```bash
mkvirtualenv --python=/usr/bin/python3.10 epargne-voyage-venv
pip install -r requirements.txt
```

(`mkvirtualenv` active automatiquement l'environnement après création — les prochaines fois qu'on ouvre
une console, on le réactive avec `workon epargne-voyage-venv`.)

## E. Configurer les variables d'environnement

Toujours dans `~/epargne-voyage`, crée le fichier `.env` :

```bash
nano .env
```

Colle ce contenu (remplace le code coach par celui que tu veux communiquer à ton coach) :

```
SECRET_KEY=d404b18c4b271d8f2648258f01b19541dc39eaf4ad2cf0d267e31a96e96614fe
DATABASE_URL=sqlite:///instance/epargne.db
COACH_NOM_DEFAUT=Coach
COACH_CODE_DEFAUT=482913
```

Sauvegarde avec `Ctrl+O` puis `Entrée`, quitte avec `Ctrl+X`.

> La `SECRET_KEY` ci-dessus a été générée aléatoirement pour ce projet — tu peux la garder, ou en générer
> une autre toi-même avec `python3 -c "import secrets; print(secrets.token_hex(32))"`.

## F. Initialiser la base de données

```bash
export FLASK_APP=wsgi:app
flask init-db
```

Tu dois voir : `Coach créé : Coach — code d'accès : 482913` (ou le code que tu as choisi).

## G. Configurer l'application web

Dans le dashboard PythonAnywhere, onglet **Web** → **Add a new web app** :

1. Choisis **Manual configuration** (pas "Flask" dans la liste guidée — on a déjà notre structure).
2. Choisis **Python 3.10**.
3. Une fois créée, dans la section **Code** :
   - **Source code** : `/home/TON_PSEUDO/epargne-voyage`
   - **Working directory** : `/home/TON_PSEUDO/epargne-voyage`
4. Dans la section **Virtualenv**, indique : `/home/TON_PSEUDO/.virtualenvs/epargne-voyage-venv`
5. Clique sur le lien **WSGI configuration file** et remplace tout le contenu par :

```python
import sys
import os

project_home = '/home/TON_PSEUDO/epargne-voyage'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

from dotenv import load_dotenv
load_dotenv(os.path.join(project_home, '.env'))

from epargne import create_app
application = create_app()
```

(remplace `TON_PSEUDO` par ton nom d'utilisateur, aux deux endroits : dans ce fichier et dans les chemins
Source code / Virtualenv ci-dessus)

6. (Optionnel mais recommandé) Section **Static files**, ajoute une entrée :
   - URL : `/static/`
   - Directory : `/home/TON_PSEUDO/epargne-voyage/epargne/static/`
7. Clique sur le gros bouton vert **Reload**.

## H. Tester

Ouvre `https://TON_PSEUDO.pythonanywhere.com` — tu devrais voir l'écran de connexion. Connecte-toi côté
coach avec le code défini à l'étape E, puis ajoute vos premiers participants.

## Mettre à jour le site plus tard

Sur ta machine, commit et push tes changements (`git push`). Puis, sur PythonAnywhere, dans une console
Bash :

```bash
cd epargne-voyage
git pull
workon epargne-voyage-venv
pip install -r requirements.txt   # seulement si requirements.txt a changé
```

Puis retourne sur l'onglet **Web** et clique **Reload**.

## À savoir sur l'offre gratuite

- L'adresse est en `TON_PSEUDO.pythonanywhere.com` (pas de domaine personnalisé sans passer à un forfait
  payant, ~5 $/mois).
- PythonAnywhere désactive les sites gratuits inactifs après 3 mois : reconnecte-toi de temps en temps et
  clique sur **"Run until 3 months from today"** dans l'onglet Web pour prolonger.
- Pense à télécharger de temps en temps `instance/epargne.db` (onglet Files) comme sauvegarde.
