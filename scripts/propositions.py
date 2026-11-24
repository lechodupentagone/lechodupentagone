"""Propositions du jour : à partir du brouillon rédigé (propositions/AAAA-MM-JJ/brouillon.json),
fabrique pour chaque sujet le visuel, le carrousel, le Reel et la page de propositions,
et prépare l'import des articles dans la Google Sheet (statut « à valider »).

  python scripts/propositions.py propositions/2026-11-24/brouillon.json

Format du brouillon (liste de sujets) :
  {"titre": "...",            # titre de l'article et du visuel (≤ 110 caractères)
   "categorie": "Municipal",  # rubrique principale (couleur), une des catégories de config.yaml
   "autres_rubriques": ["Agglo"],  # facultatif : rubriques supplémentaires
   "sources": [{"nom": "Ouest-France", "lien": "https://..."}],
   "article": "Texte en Markdown, 250 à 600 mots, rédigé avec nos mots",
   "legende_instagram": "...", "texte_facebook": "...",
   "carrousel": [{"titre": "...", "texte": "..."}],   # 3 à 5 diapos après la couverture
   "reel": ["phrase 1", "phrase 2", ...]}              # 4 à 7 phrases courtes
"""
import html
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from common import RACINE, config, identifiant, slugifier
from visual import diapo, diapo_fin, generer, image_reel

IMPORT = RACINE / "data" / "propositions_a_importer.json"
REELS = RACINE / "data" / "reels.json"      # id de la ligne → Reel, repris sur le site à la publication


def reel(phrases, categorie, date, dossier, marque):
    images, durees = [], []
    for i, p in enumerate(phrases):
        images.append(image_reel(p, categorie, date, dossier / f"reel-{i:02d}.jpg", marque, premiere=(i == 0)))
        durees.append(max(2.6, min(5.0, 0.36 * len(p.split()) + 1.2)))
    images.append(diapo_fin(categorie, dossier / "reel-fin.jpg", marque, 1080, 1920))
    durees.append(3.0)
    fondu = 0.35
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    for img, d in zip(images, durees):
        cmd += ["-loop", "1", "-t", f"{d + fondu:.2f}", "-i", str(img)]
    filtres, prec, decalage = [], "0:v", 0.0
    for k in range(1, len(images)):
        decalage += durees[k - 1]
        sortie = f"v{k}"
        filtres.append(f"[{prec}][{k}:v]xfade=transition=fade:duration={fondu}:offset={decalage:.2f}[{sortie}]")
        prec = sortie
    filtres.append(f"[{prec}]format=yuv420p,fps=30[out]")
    sortie = dossier / "reel.mp4"
    cmd += ["-filter_complex", ";".join(filtres), "-map", "[out]", "-c:v", "libx264",
            "-preset", "veryfast", "-crf", "21", "-movflags", "+faststart", str(sortie)]
    subprocess.run(cmd, check=True)
    (dossier / "reel-poster.jpg").write_bytes(images[0].read_bytes())   # affiche de la vidéo sur le site
    for img in images:
        img.unlink()
    return sortie


def bouton_copier(texte, ident):
    return (f'<div class="copie"><pre id="{ident}">{html.escape(texte)}</pre>'
            f'<button onclick="copier(\'{ident}\', this)">Copier</button></div>')


DEPOT = "https://raw.githubusercontent.com/lechodupentagone/lechodupentagone/main/propositions"


def carte(s, rel, n, jour):
    brut = f"{DEPOT}/{jour}/{rel}"   # téléchargement depuis GitHub (le cadre de la page bloque <a download>)
    srcs = " · ".join(f'<a href="{html.escape(x["lien"])}" target="_blank">{html.escape(x["nom"])}</a>'
                      for x in s["sources"])
    diapos = "".join(f'<a href="{brut}/{f}" target="_blank"><img src="{rel}/{f}" alt=""></a>' for f in s["_carrousel"])
    return f"""
<section class="sujet">
  <p class="cat">{html.escape(s['categorie'])}</p>
  <h2>{n}. {html.escape(s['titre'])}</h2>
  <p class="sources">Sources : {srcs}</p>
  <div class="grille">
    <div><h3>Visuel</h3><img src="{rel}/visuel.jpg" alt="">
      <a class="dl" href="{brut}/visuel.jpg" target="_blank">Télécharger ↗</a></div>
    <div><h3>Reel</h3><video src="{rel}/reel.mp4" controls playsinline muted></video>
      <a class="dl" href="{brut}/reel.mp4" target="_blank">Télécharger la vidéo ↗</a>
      <p class="astuce">Ajoute une musique dans Instagram au moment de poster.</p></div>
  </div>
  <h3>Carrousel ({len(s['_carrousel'])} images, dans l'ordre — clique sur une image pour la télécharger)</h3>
  <div class="carrousel">{diapos}</div>
  <h3>Légende Instagram</h3>{bouton_copier(s['legende_instagram'], f'ig{n}')}
  <h3>Texte Facebook</h3>{bouton_copier(s['texte_facebook'], f'fb{n}')}
  <details><summary>Article proposé pour le site</summary><div class="article">{html.escape(s['article'])}</div></details>
</section>"""


PAGE = """<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Propositions du {date} — L'Écho du Pentagone</title>
<style>
:root{{--nuit:#0B1F3A;--jaune:#FFC233}}
*{{box-sizing:border-box}}body{{margin:0;font:16px/1.5 system-ui,-apple-system,Segoe UI,sans-serif;background:#F3F4F6;color:#111}}
header{{background:var(--nuit);color:#fff;padding:28px 20px}}header h1{{margin:0;font-size:26px}}
header p{{margin:6px 0 0;color:var(--jaune)}}main{{max-width:920px;margin:0 auto;padding:16px}}
.mode{{background:#fff;border-left:5px solid var(--jaune);padding:12px 16px;margin:16px 0;border-radius:6px}}
.sujet{{background:#fff;border-radius:12px;padding:20px;margin:22px 0;box-shadow:0 1px 3px #0001}}
.cat{{display:inline-block;background:var(--nuit);color:#fff;border-radius:99px;padding:2px 12px;font-size:13px;font-weight:700;margin:0}}
h2{{margin:10px 0 4px;font-size:22px}}h3{{font-size:15px;margin:18px 0 6px;color:#374151}}
.sources{{font-size:14px;color:#4B5563}}.grille{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
img,video{{width:100%;border-radius:8px;display:block}}video{{max-height:520px;background:#000}}
.carrousel{{display:flex;gap:8px;overflow-x:auto}}.carrousel img{{width:150px;flex:none}}
.dl{{display:inline-block;margin-top:6px;font-weight:600;color:var(--nuit)}}.astuce{{font-size:13px;color:#6B7280;margin:4px 0}}
.copie{{position:relative}}pre{{white-space:pre-wrap;background:#F9FAFB;border:1px solid #E5E7EB;border-radius:8px;padding:12px;margin:0;font:15px/1.5 system-ui,sans-serif}}
button{{position:absolute;top:8px;right:8px;background:var(--nuit);color:#fff;border:0;border-radius:6px;padding:6px 12px;cursor:pointer}}
details{{margin-top:14px}}summary{{cursor:pointer;font-weight:600}}.article{{white-space:pre-wrap;padding:10px 0}}
@media(max-width:640px){{.grille{{grid-template-columns:1fr}}}}
</style></head><body>
<header><h1>Propositions du {date_longue}</h1><p>L'Écho du Pentagone · {nb} sujet(s)</p></header>
<main>
<div class="mode"><b>Mode d'emploi.</b> Pour chaque sujet, télécharge le visuel, le carrousel ou le Reel, copie la légende, et poste toi-même sur Instagram et Facebook.
Pour publier l'article sur le site, coche « publier » sur sa ligne dans la Google Sheet (type « proposition Écho »).</div>
{cartes}
</main>
<script>
function copier(id, b){{const t=document.getElementById(id).innerText;
(navigator.clipboard?navigator.clipboard.writeText(t):Promise.reject()).then(()=>{{b.textContent='Copié ✓';setTimeout(()=>b.textContent='Copier',1500)}})
.catch(()=>{{const r=document.createRange();r.selectNodeContents(document.getElementById(id));const s=getSelection();s.removeAllRanges();s.addRange(r);b.textContent='Sélectionné : Ctrl+C'}})}}
</script></body></html>"""

MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
        "septembre", "octobre", "novembre", "décembre"]
JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]


def main(chemin_brouillon):
    brouillon = Path(chemin_brouillon).resolve()
    dossier_jour = brouillon.parent
    sujets = json.loads(brouillon.read_text(encoding="utf-8"))
    marque = config()["marque"]
    jour = datetime.strptime(dossier_jour.name[:10], "%Y-%m-%d")
    date = f"{jour:%d/%m/%Y}"
    a_importer = json.loads(IMPORT.read_text()) if IMPORT.exists() else []
    reels = json.loads(REELS.read_text()) if REELS.exists() else {}
    cartes = []
    for n, s in enumerate(sujets, start=1):
        slug = slugifier(s["titre"], 50)
        d = dossier_jour / f"{n:02d}-{slug}"
        source_visuel = ", ".join(x["nom"] for x in s["sources"])
        generer(s["titre"], s["categorie"], source_visuel, date, d / "visuel.jpg", marque)
        # carrousel : couverture = visuel, puis diapos, puis appel à s'abonner
        total = len(s["carrousel"]) + 2
        fichiers = ["carrousel-01.jpg"]
        (d / "carrousel-01.jpg").write_bytes((d / "visuel.jpg").read_bytes())
        for k, dp in enumerate(s["carrousel"], start=2):
            diapo(k, total, dp.get("titre", ""), dp["texte"], s["categorie"], d / f"carrousel-{k:02d}.jpg", marque)
            fichiers.append(f"carrousel-{k:02d}.jpg")
        diapo_fin(s["categorie"], d / f"carrousel-{total:02d}.jpg", marque)
        fichiers.append(f"carrousel-{total:02d}.jpg")
        s["_carrousel"] = fichiers
        reel(s["reel"], s["categorie"], date, d, marque)
        cartes.append(carte(s, d.name, n, dossier_jour.name))
        sources = " · ".join(x["nom"] for x in s["sources"])
        liens = "\n".join(f"- [{x['nom']}]({x['lien']})" for x in s["sources"])
        ident = identifiant(s["sources"][0]["lien"], s["titre"])
        reels[ident] = str((d / "reel.mp4").relative_to(RACINE))
        a_importer.append({
            "id": ident,
            "source": sources, "type": "proposition Écho", "catégorie": ", ".join([s["categorie"]] + s.get("autres_rubriques", [])),
            "titre": s["titre"], "lien": s["sources"][0]["lien"],
            "texte à publier": f"{s['article'].strip()}\n\n**Sources :**\n{liens}",
        })
        print("Prêt :", s["titre"])
    page = PAGE.format(date=date, nb=len(sujets), cartes="".join(cartes),
                       date_longue=f"{JOURS[jour.weekday()]} {jour.day} {MOIS[jour.month - 1]} {jour.year}")
    (dossier_jour / "index.html").write_text(page, encoding="utf-8")
    IMPORT.parent.mkdir(exist_ok=True)
    IMPORT.write_text(json.dumps(a_importer, ensure_ascii=False, indent=1), encoding="utf-8")
    REELS.write_text(json.dumps(reels, ensure_ascii=False, indent=1), encoding="utf-8")
    print("Page :", dossier_jour / "index.html")


if __name__ == "__main__":
    main(sys.argv[1])
