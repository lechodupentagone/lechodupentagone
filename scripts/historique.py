"""Articles d'historique (antidatés) : préparation, page de relecture, puis publication.

  python scripts/historique.py preparer        → historique/attente/ (articles + visuels) et historique/relecture/index.html
  python scripts/historique.py publier 3 7     → publie tout sauf les numéros 3 et 7
"""
import html
import json
import shutil
import sys
from datetime import datetime

from common import RACINE, config, slugifier
from visual import generer

DOSSIER = RACINE / "historique"
ATTENTE = DOSSIER / "attente"


def articles():
    return json.loads((DOSSIER / "brouillon.json").read_text(encoding="utf-8"))


def fichiers(a):
    date = datetime.strptime(a["date"], "%Y-%m-%d %H:%M")
    slug = slugifier(a["titre"])
    return date, slug, f"{date:%Y-%m-%d}-{slug}"


def preparer():
    marque = config()["marque"]
    if ATTENTE.exists():
        shutil.rmtree(ATTENTE)
    cartes = []
    for n, a in enumerate(articles(), start=1):
        date, slug, base = fichiers(a)
        rubs = [a["categorie"]] + a.get("autres_rubriques", [])
        sources = " · ".join(s["nom"] for s in a["sources"])
        image = f"assets/visuels/{base}.jpg"
        generer(a["titre"], a["categorie"], sources, f"{date:%d/%m/%Y}", ATTENTE / image, marque)
        liens = "\n".join(f"- [{s['nom']}]({s['lien']})" if s["lien"] else f"- {s['nom']}" for s in a["sources"])
        titre = a["titre"].replace('"', "'")
        (ATTENTE / "_posts").mkdir(parents=True, exist_ok=True)
        (ATTENTE / "_posts" / f"{base}.md").write_text(f"""---
layout: post
title: "{titre}"
date: {date:%Y-%m-%d %H:%M:%S} +0100
categorie: "{a['categorie']}"
rubriques: [{", ".join('"' + r + '"' for r in rubs)}]
source: "{sources}"
lien_source: "{a['sources'][0]['lien']}"
image: "/{image}"
---
{a['article'].strip()}

**Sources :**
{liens}
""", encoding="utf-8")
        srcs = " · ".join(f'<a href="{html.escape(s["lien"])}" target="_blank">{html.escape(s["nom"])}</a>' if s["lien"] else html.escape(s["nom"]) for s in a["sources"])
        cartes.append(f"""
<article class="art">
  <div class="num">{n}</div>
  <img src="{image}" alt="">
  <div class="txt">
    <p class="meta">{date:%d/%m/%Y} · {" · ".join(html.escape(r) for r in rubs)}</p>
    <h2>{html.escape(a['titre'])}</h2>
    <p class="sources">Sources : {srcs}</p>
    <details><summary>Lire l'article</summary><div class="corps">{html.escape(a['article'])}</div></details>
  </div>
</article>""")
    page = f"""<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Historique à relire — L'Écho du Pentagone</title>
<style>
*{{box-sizing:border-box;min-width:0}}body{{margin:0;font:16px/1.55 system-ui,sans-serif;background:#081a31;color:#eef3fa}}
header{{padding:28px 20px 8px;max-width:980px;margin:0 auto}}h1{{margin:0 0 8px;font-size:28px}}
.mode{{background:#0f2747;border-left:5px solid #FFC233;padding:12px 16px;border-radius:8px;margin:12px 0 6px}}
main{{max-width:980px;margin:0 auto;padding:8px 20px 40px}}
.art{{display:grid;grid-template-columns:44px 150px minmax(0,1fr);gap:16px;background:#0f2747;border:1px solid #1e3a63;border-radius:12px;padding:14px;margin:14px 0;align-items:start}}
.num{{font:900 26px/1 system-ui;color:#FFC233;text-align:center;padding-top:4px}}
.art img{{width:150px;border-radius:8px}}.meta{{margin:0;color:#a9b8cf;font-size:14px}}
h2{{font-size:19px;margin:4px 0 6px;line-height:1.25}}.sources{{font-size:14px;color:#a9b8cf;margin:0 0 6px}}
a{{color:#FFC233}}summary{{cursor:pointer;font-weight:600}}.corps{{white-space:pre-wrap;padding-top:8px;color:#d6e0ee}}
@media(max-width:640px){{.art{{grid-template-columns:34px minmax(0,1fr)}}.art img{{display:none}}}}
</style></head><body>
<header><h1>Historique : {len(cartes)} articles à relire</h1>
<div class="mode">Ces articles ne sont pas encore en ligne. Ils seront publiés à leur date d'origine (fin septembre → 24 novembre).
Réponds-moi simplement « publie tout » ou « publie sauf 3 et 7 », avec d'éventuelles corrections.</div></header>
<main>{"".join(cartes)}</main></body></html>"""
    (ATTENTE / "index.html").write_text(page, encoding="utf-8")
    print(f"{len(cartes)} articles prêts dans {ATTENTE}")


def publier(exclus):
    for n, a in enumerate(articles(), start=1):
        if n in exclus:
            continue
        _, _, base = fichiers(a)
        shutil.copyfile(ATTENTE / "_posts" / f"{base}.md", RACINE / "site" / "_posts" / f"{base}.md")
        shutil.copyfile(ATTENTE / "assets" / "visuels" / f"{base}.jpg", RACINE / "site" / "assets" / "visuels" / f"{base}.jpg")
        print("Publié :", a["titre"])


if __name__ == "__main__":
    if sys.argv[1] == "preparer":
        preparer()
    elif sys.argv[1] == "publier":
        publier({int(x) for x in sys.argv[2:]})
