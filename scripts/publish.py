"""Publication des éléments validés (case « publier » cochée dans la Google Sheet).

  python scripts/publish.py preparer   → crée le visuel + l'article du site,
                                         note les éléments dans data/a_publier.json
  python scripts/publish.py reseaux    → publie sur Facebook et Instagram
                                         (après mise en ligne du site, car Instagram
                                         va chercher l'image à son adresse publique)
  python scripts/publish.py essai "Titre" "Catégorie" "Source"  → génère un visuel de test
  python scripts/publish.py identite   → photo de profil + bannière Facebook
"""
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

from common import COLONNES, RACINE, config, feuille, slugifier
from visual import couverture, generer, logo

FICHIER_FILE = RACINE / "data" / "a_publier.json"
API = "https://graph.facebook.com/" + os.environ.get("META_API_VERSION", "v23.0")
OUI = {"TRUE", "VRAI", "OUI", "X", "1"}


def lettre(col):
    return chr(ord("A") + COLONNES.index(col))


def maj(onglet, ligne, valeurs):
    for col, val in valeurs.items():
        onglet.update_acell(f"{lettre(col)}{ligne}", val)


def texte_de(e):
    return (e.get("texte à publier") or e.get("titre") or "").strip()


def ecrire_article(e, slug, date, image_rel, cfg):
    dossier = RACINE / "site" / "_posts"
    dossier.mkdir(parents=True, exist_ok=True)
    titre = e["titre"].replace('"', "'")
    corps = texte_de(e)
    contenu = f"""---
layout: post
title: "{titre}"
date: {date:%Y-%m-%d %H:%M:%S} +0100
categorie: "{e.get('catégorie', '')}"
source: "{e.get('source', '')}"
lien_source: "{e.get('lien', '')}"
image: "/{image_rel}"
---
{corps}

Source : [{e.get('source', '')}]({e.get('lien', '')})
"""
    (dossier / f"{date:%Y-%m-%d}-{slug}.md").write_text(contenu, encoding="utf-8")


def preparer():
    cfg = config()
    marque = cfg["marque"]
    onglet = feuille()
    valeurs = onglet.get_all_values()
    entete, lignes = valeurs[0], valeurs[1:]
    file_attente = json.loads(FICHIER_FILE.read_text()) if FICHIER_FILE.exists() else []

    for i, brut in enumerate(lignes, start=2):
        e = dict(zip(entete, brut + [""] * (len(entete) - len(brut))))
        if e.get("publier", "").strip().upper() not in OUI or e.get("statut") != "à valider":
            continue
        date = datetime.now()
        slug = slugifier(e["titre"])
        image_rel = f"assets/visuels/{date:%Y-%m-%d}-{slug}.jpg"
        generer(e["titre"], e.get("catégorie") or "Info", e.get("source", ""),
                f"{date:%d/%m/%Y}", RACINE / "site" / image_rel, marque)
        ecrire_article(e, slug, date, image_rel, cfg)
        url_article = f"{marque['site_url']}/{date:%Y/%m}/{slug}/"
        maj(onglet, i, {"statut": "en ligne (site)", "url site": url_article})
        file_attente.append({"ligne": i, "texte": texte_de(e), "source": e.get("source", ""),
                             "url_article": url_article,
                             "url_image": f"{marque['site_url']}/{image_rel}"})
        print("Préparé :", e["titre"])

    FICHIER_FILE.parent.mkdir(parents=True, exist_ok=True)
    FICHIER_FILE.write_text(json.dumps(file_attente, ensure_ascii=False, indent=1))


def attendre_url(url, minutes=10):
    fin = time.time() + minutes * 60
    while time.time() < fin:
        if requests.head(url, timeout=20).status_code == 200:
            return True
        time.sleep(20)
    return False


def publier_facebook(texte, url_image):
    r = requests.post(f"{API}/{os.environ['META_PAGE_ID']}/photos", data={
        "url": url_image, "message": texte, "access_token": os.environ["META_PAGE_TOKEN"]},
        timeout=60)
    r.raise_for_status()
    return r.json().get("post_id") or r.json().get("id")


def publier_instagram(texte, url_image):
    ig, jeton = os.environ["IG_USER_ID"], os.environ["META_PAGE_TOKEN"]
    r = requests.post(f"{API}/{ig}/media", data={
        "image_url": url_image, "caption": texte, "access_token": jeton}, timeout=60)
    r.raise_for_status()
    creation = r.json()["id"]
    for _ in range(30):                       # attendre que Meta ait traité l'image
        etat = requests.get(f"{API}/{creation}", params={
            "fields": "status_code", "access_token": jeton}, timeout=30).json()
        if etat.get("status_code") == "FINISHED":
            break
        time.sleep(5)
    r = requests.post(f"{API}/{ig}/media_publish", data={
        "creation_id": creation, "access_token": jeton}, timeout=60)
    r.raise_for_status()
    return r.json()["id"]


def reseaux():
    if not FICHIER_FILE.exists():
        return
    file_attente = json.loads(FICHIER_FILE.read_text())
    if not file_attente:
        return
    onglet = feuille()
    restants = []
    for item in file_attente:
        if not attendre_url(item["url_image"]):
            print("Image pas encore en ligne, nouvel essai au prochain passage :", item["url_image"])
            restants.append(item)
            continue
        legende = f"{item['texte']}\n\nSource : {item['source']}\n👉 {item['url_article']}"
        res = {}
        try:
            if os.environ.get("META_PAGE_ID"):
                res["facebook"] = publier_facebook(legende, item["url_image"])
            if os.environ.get("IG_USER_ID"):
                # les liens ne sont pas cliquables sur Instagram : on renvoie vers le site
                res["instagram"] = publier_instagram(
                    f"{item['texte']}\n\nSource : {item['source']}\nArticle complet : lien en bio",
                    item["url_image"])
            res.update({"statut": "publié", "publié le": datetime.now().strftime("%Y-%m-%d %H:%M")})
        except requests.HTTPError as exc:
            res["statut"] = f"erreur réseaux : {exc.response.text[:200]}"
        maj(onglet, item["ligne"], res)
        print("Publié :", item["texte"][:60], res)
    FICHIER_FILE.write_text(json.dumps(restants, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else ""
    if action == "preparer":
        preparer()
    elif action == "reseaux":
        reseaux()
    elif action == "essai":
        titre, cat, src = (sys.argv[2:5] + ["Titre d'essai", "Municipal", "Essai"])[:3]
        chemin = generer(titre, cat, src, datetime.now().strftime("%d/%m/%Y"),
                         RACINE / "essai.jpg", config()["marque"])
        print("Visuel généré :", chemin)
    elif action == "identite":
        m = config()["marque"]
        print(logo(RACINE / "site" / "assets" / "identite" / "logo.png", m))
        print(couverture(RACINE / "site" / "assets" / "identite" / "couverture-facebook.png", m))
    else:
        print(__doc__)
