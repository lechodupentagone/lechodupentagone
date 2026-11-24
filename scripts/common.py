"""Fonctions partagées : configuration, état local, accès à la Google Sheet."""
import hashlib
import json
import os
import re
import unicodedata
from pathlib import Path

import yaml

RACINE = Path(__file__).resolve().parent.parent
FICHIER_VUS = RACINE / "data" / "vus.json"

# Colonnes de l'onglet « File de validation » de la Google Sheet (dans cet ordre)
COLONNES = [
    "id", "collecté le", "source", "type", "catégorie", "titre", "lien",
    "pdf", "texte à publier", "publier", "statut", "publié le",
    "url site", "facebook", "instagram",
]


def config():
    with open(RACINE / "config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def slugifier(texte, longueur=60):
    t = unicodedata.normalize("NFKD", texte).encode("ascii", "ignore").decode()
    t = re.sub(r"[^a-zA-Z0-9]+", "-", t).strip("-").lower()
    return t[:longueur].strip("-") or "article"


def identifiant(lien, titre):
    base = (lien or "") + "|" + normaliser_titre(titre)
    return hashlib.sha1(base.encode()).hexdigest()[:12]


def normaliser_titre(titre):
    t = (titre or "").rsplit(" - ", 1)[0] if " - " in (titre or "") else (titre or "")
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


def charger_vus():
    if FICHIER_VUS.exists():
        return json.loads(FICHIER_VUS.read_text(encoding="utf-8"))
    return {"ids": [], "titres": []}


def sauver_vus(vus):
    FICHIER_VUS.parent.mkdir(parents=True, exist_ok=True)
    vus["ids"] = vus["ids"][-5000:]
    vus["titres"] = vus["titres"][-5000:]
    FICHIER_VUS.write_text(json.dumps(vus, ensure_ascii=False, indent=0), encoding="utf-8")


def feuille():
    """Ouvre l'onglet « File de validation ». Nécessite les secrets
    GOOGLE_SERVICE_ACCOUNT_JSON et SHEET_ID."""
    import gspread

    info = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])
    client = gspread.service_account_from_dict(info)
    classeur = client.open_by_key(os.environ["SHEET_ID"])
    try:
        onglet = classeur.worksheet("File de validation")
    except gspread.WorksheetNotFound:
        onglet = classeur.add_worksheet("File de validation", rows=2000, cols=len(COLONNES))
    if onglet.row_values(1) != COLONNES:
        onglet.update(range_name="A1", values=[COLONNES])
    return onglet
