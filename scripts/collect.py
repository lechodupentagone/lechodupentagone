"""Collecte : lit les flux, filtre, dédoublonne et ajoute les nouveautés
dans l'onglet « File de validation » de la Google Sheet.

Usage :  python scripts/collect.py            (écrit dans la Google Sheet)
         python scripts/collect.py --essai    (affiche sans rien écrire)
"""
import re
import sys
import time
from datetime import datetime, timedelta, timezone

import feedparser
import requests

from common import (COLONNES, RACINE, charger_vus, config, feuille, identifiant,
                    normaliser_titre, sauver_vus, slugifier)

UA = {"User-Agent": "Mozilla/5.0 (veille locale; contact dans config.yaml)"}
COMMUNES_AGGLO = ["aubigny", "clouzeaux", "dompierre", "fougere", "chaize", "ferriere",
                  "landeronde", "tablier", "mouilleron", "nesmy", "rives de l yon",
                  "thorigny", "venansault"]


def lire_flux(url):
    r = requests.get(url, headers=UA, timeout=30)
    r.raise_for_status()
    return feedparser.parse(r.content)


def date_entree(e):
    for cle in ("published_parsed", "updated_parsed"):
        if e.get(cle):
            return datetime.fromtimestamp(time.mktime(e[cle]), tz=timezone.utc)
    return datetime.now(timezone.utc)


def lien_pdf(e):
    html = " ".join(c.get("value", "") for c in e.get("content", [])) + e.get("summary", "")
    m = re.search(r'href="\s*(https?://[^"]+?\.pdf)"', html)
    return m.group(1).strip() if m else ""


def categorie_acte(titre, cfg):
    slug = slugifier(titre, 200)
    if any(x in slug for x in cfg.get("actes_exclure", [])):
        return None
    for cat, mots in cfg["actes_mots_cles"].items():
        if any(m in slug for m in mots):
            return cat
    return None


def humaniser_acte(titre):
    """« 2026-Ville-3772-souscription-dun-emprunt-de-25-me » →
    « Ville — souscription d'un emprunt de 25 me (n° 2026-Ville-3772) »"""
    m = re.match(r"(\d{4})-(Ville|Agglo|CCAS|CIAS)-(\d+)-(.*)", titre)
    if not m:
        return titre
    annee, entite, num, reste = m.groups()
    reste = reste.replace("-", " ").replace("dun ", "d'un ").replace("dune ", "d'une ")
    return f"{entite} — {reste} (arrêté n° {annee}-{entite}-{num})"


def categorie_presse(titre):
    t = normaliser_titre(titre)
    if any(c in t for c in COMMUNES_AGGLO):
        return "Agglo"
    if "roche sur yon" in t or "yonnais" in t:
        return "Municipal"
    return "Vendée"


def titre_propre(titre):
    return titre.rsplit(" - ", 1)[0].strip() if " - " in titre else titre.strip()  # retire « - Source »


def archiver_pdf(url):
    dossier = RACINE / "archives" / "actes"
    dossier.mkdir(parents=True, exist_ok=True)
    nom = re.sub(r"^\d{4}-\d{2}-\d{2}_[\d:]+-[ap]m_", "", url.rsplit("/", 1)[-1])  # retire l'horodatage
    cible = dossier / re.sub(r"[^A-Za-z0-9._-]", "_", nom)
    if not cible.exists():
        r = requests.get(url, headers=UA, timeout=60)
        r.raise_for_status()
        cible.write_bytes(r.content)
    return str(cible.relative_to(RACINE))


def collecter(cfg, vus):
    limite = datetime.now(timezone.utc) - timedelta(days=cfg["collecte"]["max_age_jours"])
    nouveaux, erreurs = [], []
    titres_vus = set(vus["titres"])
    ids_vus = set(vus["ids"])

    for src in cfg["sources"]:
        urls = [src["url"]]
        if src["type"] == "actes":
            urls += [f"{src['url']}?paged={p}" for p in range(2, cfg["collecte"]["pages_actes"] + 1)]
        for url in urls:
            try:
                flux = lire_flux(url)
            except Exception as exc:  # une source en panne ne bloque pas les autres
                erreurs.append(f"{src['nom']} : {exc}")
                continue
            for e in flux.entries:
                titre = e.get("title", "").strip()
                lien = e.get("link", "").strip()
                if not titre or date_entree(e) < limite:
                    continue
                uid = identifiant(lien, titre)
                cle_titre = normaliser_titre(titre)
                if uid in ids_vus or cle_titre in titres_vus:
                    continue
                ids_vus.add(uid)
                titres_vus.add(cle_titre)
                vus["ids"].append(uid)
                vus["titres"].append(cle_titre)

                if src["type"] == "actes":
                    cat_acte = categorie_acte(titre, cfg)
                    if not cat_acte:
                        continue                     # acte de routine : ignoré
                    pdf = lien_pdf(e)
                    if pdf and cfg.get("archiver_pdf_actes"):
                        try:
                            pdf = archiver_pdf(pdf)
                        except Exception as exc:
                            erreurs.append(f"PDF {titre} : {exc}")
                    entite = "Agglo" if "-Agglo-" in titre else "Municipal"
                    nouveaux.append({
                        "id": uid, "source": src["nom"], "type": f"acte · {cat_acte}",
                        "catégorie": entite, "titre": humaniser_acte(titre), "lien": lien,
                        "pdf": pdf, "texte à publier": "",
                    })
                else:
                    if any(x.lower() in titre.lower() for x in cfg.get("presse_exclure", [])):
                        continue
                    propre = titre_propre(titre)
                    nouveaux.append({
                        "id": uid, "source": src["nom"], "type": src["type"],
                        "catégorie": categorie_presse(titre), "titre": propre, "lien": lien,
                        "pdf": "", "texte à publier": "",
                    })
    return nouveaux, erreurs


def main():
    essai = "--essai" in sys.argv
    cfg = config()
    vus = charger_vus()
    nouveaux, erreurs = collecter(cfg, vus)
    maintenant = datetime.now().strftime("%Y-%m-%d %H:%M")
    lignes = []
    for n in nouveaux:
        n.update({"collecté le": maintenant, "publier": False, "statut": "à valider"})
        lignes.append([n.get(c, "") for c in COLONNES])

    print(f"{len(nouveaux)} nouvel(s) élément(s), {len(erreurs)} erreur(s)")
    for err in erreurs:
        print("  ⚠", err)
    if essai:
        for n in nouveaux:
            print(f"  [{n['type']}] {n['titre']}  ->  {n['lien']}")
        return
    if lignes:
        feuille().append_rows(lignes, value_input_option="USER_ENTERED")
    sauver_vus(vus)


if __name__ == "__main__":
    main()
