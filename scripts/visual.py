"""Visuels de L'Écho du Pentagone.

- generer() : visuel d'une publication, 1080 × 1350 (portrait Instagram / Facebook)
- logo()    : photo de profil 1080 × 1080
Couleurs par catégorie dans config.yaml (marque.categories).
"""
import math

from PIL import Image, ImageDraw, ImageFont

from common import RACINE

POLICES = RACINE / "assets" / "fonts"
L, H = 1080, 1350
M = 84  # marge


def police(nom, taille):
    return ImageFont.truetype(str(POLICES / nom), taille)


def pentagone(cx, cy, r, rotation=-90):
    return [(cx + r * math.cos(math.radians(rotation + 72 * k)),
             cy + r * math.sin(math.radians(rotation + 72 * k))) for k in range(5)]


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def echo(img, cx, cy, rayons, largeur, opacite):
    """Pentagones concentriques semi-transparents : l'« écho »."""
    calque = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(calque)
    for i, r in enumerate(rayons):
        a = int(255 * opacite * (1 - i / (len(rayons) + 1)))
        pts = pentagone(cx, cy, r)
        d.line(pts + [pts[0]], fill=(255, 255, 255, a), width=largeur, joint="curve")
    img.alpha_composite(calque)


def marque_logo(d, x, y, taille, couleur):
    """Petit logo : pentagone plein + deux échos."""
    cx, cy = x + taille / 2, y + taille / 2 + taille * 0.04
    d.polygon(pentagone(cx, cy, taille * 0.22), fill=couleur)
    for r, w in ((taille * 0.36, max(2, taille // 18)), (taille * 0.5, max(2, taille // 22))):
        pts = pentagone(cx, cy, r)
        d.line(pts + [pts[0]], fill=couleur, width=w, joint="curve")


def couper(d, texte, fnt, largeur):
    lignes, ligne = [], ""
    for mot in texte.split():
        essai = f"{ligne} {mot}".strip()
        if d.textlength(essai, font=fnt) <= largeur:
            ligne = essai
        else:
            if ligne:
                lignes.append(ligne)
            ligne = mot
    return lignes + ([ligne] if ligne else [])


def texte_espace(d, xy, texte, fnt, fill, espacement):
    x, y = xy
    for c in texte:
        d.text((x, y), c, font=fnt, fill=fill)
        x += d.textlength(c, font=fnt) + espacement
    return x


def couleur_categorie(categorie, marque):
    return marque.get("categories", {}).get(categorie, marque["couleur_fond"])


def generer(titre, categorie, source, date, chemin, marque):
    fond = couleur_categorie(categorie, marque)
    img = Image.new("RGBA", (L, H), hex_rgb(fond) + (255,))
    echo(img, L - 60, H - 250, [260, 400, 540, 680], 10, 0.22)
    d = ImageDraw.Draw(img)
    blanc = (255, 255, 255)

    # En-tête : logo + nom, date à droite
    marque_logo(d, M - 6, 66, 64, blanc)
    texte_espace(d, (M + 74, 80), marque["nom"].upper(), police("InterDisplay-ExtraBold.otf", 30), blanc, 2)
    f_date = police("InterDisplay-Medium.otf", 28)
    d.text((L - M - d.textlength(date, font=f_date), 82), date, font=f_date, fill=blanc)

    # Étiquette de catégorie (pastille blanche, texte couleur de fond)
    f_cat = police("InterDisplay-Bold.otf", 30)
    cat = categorie.upper()
    y_cat = 250
    w = sum(d.textlength(c, font=f_cat) + 2 for c in cat)
    d.rounded_rectangle([M, y_cat, M + w + 44, y_cat + 58], radius=29, fill=blanc)
    texte_espace(d, (M + 22, y_cat + 11), cat, f_cat, hex_rgb(fond), 2)

    # Titre : le plus grand possible dans la zone
    haut, bas = y_cat + 110, H - 230
    for taille in range(112, 50, -4):
        f_titre = police("InterDisplay-Black.otf", taille)
        lignes = couper(d, titre, f_titre, L - 2 * M)
        pas = int(taille * 1.08)
        if len(lignes) * pas <= bas - haut and max(d.textlength(x, font=f_titre) for x in lignes) <= L - 2 * M:
            break
    y = haut
    for ligne in lignes:
        d.text((M, y), ligne, font=f_titre, fill=blanc)
        y += pas

    # Pied : source à gauche, compte à droite
    d.rectangle([M, H - 170, M + 90, H - 162], fill=blanc)
    f_pied = police("InterDisplay-Medium.otf", 30)
    f_compte = police("InterDisplay-Bold.otf", 30)
    src = f"Source : {source}"
    while d.textlength(src, font=f_pied) > L - 2 * M - 360:
        src = src[:-2].rstrip() + "…"
    d.text((M, H - 132), src, font=f_pied, fill=blanc)
    compte = marque.get("compte", "")
    d.text((L - M - d.textlength(compte, font=f_compte), H - 132), compte, font=f_compte, fill=blanc)

    chemin.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(chemin, "JPEG", quality=92)   # Instagram n'accepte que le JPEG
    return chemin


def logo(chemin, marque, taille=1080):
    """Photo de profil : le signe seul (lisible en petit, tient dans le cercle d'Instagram)."""
    img = Image.new("RGBA", (taille, taille), hex_rgb(marque["couleur_fond"]) + (255,))
    c = taille / 2
    cy = c + taille * 0.03                     # centre optique du pentagone
    echo(img, c, cy, [taille * 0.255, taille * 0.355], int(taille / 42), 0.95)
    d = ImageDraw.Draw(img)
    d.polygon(pentagone(c, cy, taille * 0.15), fill=hex_rgb(marque["couleur_accent"]))
    chemin.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(chemin, "PNG")
    return chemin


def couverture(chemin, marque, l=1640, h=624):
    """Bannière Facebook : signe + nom + accroche (zone utile centrée)."""
    img = Image.new("RGBA", (l, h), hex_rgb(marque["couleur_fond"]) + (255,))
    echo(img, l - 180, h / 2 + 40, [220, 330, 440, 550], 8, 0.18)
    d = ImageDraw.Draw(img)
    x0, cy = 330, h / 2
    marque_logo(d, x0 - 150, cy - 75, 150, (255, 255, 255))
    d.polygon(pentagone(x0 - 75, cy + 6, 150 * 0.22), fill=hex_rgb(marque["couleur_accent"]))
    blanc = (255, 255, 255)
    d.text((x0 + 30, cy - 92), "L'ÉCHO DU", font=police("InterDisplay-Bold.otf", 48), fill=blanc)
    d.text((x0 + 26, cy - 46), "PENTAGONE", font=police("InterDisplay-Black.otf", 104), fill=blanc)
    d.text((x0 + 30, cy + 78), marque["accroche"], font=police("InterDisplay-Medium.otf", 36),
           fill=hex_rgb(marque["couleur_accent"]))
    chemin.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(chemin, "PNG")
    return chemin


# ------------------------------------------------------------------
#  Carrousel (1080 × 1350) et Reel (1080 × 1920)
# ------------------------------------------------------------------
def _entete(d, marque, blanc, largeur, droite=""):
    marque_logo(d, M - 6, 66, 64, blanc)
    texte_espace(d, (M + 74, 80), marque["nom"].upper(), police("InterDisplay-ExtraBold.otf", 30), blanc, 2)
    if droite:
        f = police("InterDisplay-Medium.otf", 28)
        d.text((largeur - M - d.textlength(droite, font=f), 82), droite, font=f, fill=blanc)


def _bloc(d, texte, nom_police, tailles, largeur, hauteur, interligne=1.12):
    """Plus grande taille de police qui fait tenir le texte dans la zone."""
    for taille in tailles:
        fnt = police(nom_police, taille)
        lignes = []
        for para in texte.split("\n"):
            lignes += couper(d, para, fnt, largeur) or [""]
        pas = int(taille * interligne)
        if len(lignes) * pas <= hauteur and max(d.textlength(x, font=fnt) for x in lignes) <= largeur:
            break
    return fnt, lignes, pas


def diapo(numero, total, sous_titre, texte, categorie, chemin, marque):
    """Diapo intérieure du carrousel : fond bleu nuit, numéro, intertitre jaune, texte."""
    fond = hex_rgb(marque["couleur_fond"])
    accent = hex_rgb(marque["couleur_accent"])
    teinte = hex_rgb(couleur_categorie(categorie, marque))
    img = Image.new("RGBA", (L, H), fond + (255,))
    echo(img, L + 40, -40, [260, 400, 540], 8, 0.10)
    d = ImageDraw.Draw(img)
    blanc = (255, 255, 255)
    _entete(d, marque, blanc, L, f"{numero}/{total}")
    d.rectangle([M, 230, M + 120, 240], fill=teinte if teinte != fond else accent)
    y = 290
    if sous_titre:
        f, lignes, pas = _bloc(d, sous_titre, "InterDisplay-Black.otf", range(80, 46, -4), L - 2 * M, 300)
        for l_ in lignes:
            d.text((M, y), l_, font=f, fill=accent)
            y += pas
        y += 40
    f, lignes, pas = _bloc(d, texte, "InterDisplay-Medium.otf", range(62, 28, -2), L - 2 * M, H - 200 - y, 1.32)
    for l_ in lignes:
        d.text((M, y), l_, font=f, fill=blanc)
        y += pas
    f_c = police("InterDisplay-Bold.otf", 30)
    compte = marque.get("compte", "")
    d.text((L - M - d.textlength(compte, font=f_c), H - 132), compte, font=f_c, fill=blanc)
    if numero < total:
        d.text((M, H - 132), "Glissez →", font=police("InterDisplay-Medium.otf", 30), fill=accent)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(chemin, "JPEG", quality=92)
    return chemin


def diapo_fin(categorie, chemin, marque, l=L, h=H):
    """Dernière diapo / dernière image du Reel : appel à s'abonner."""
    fond = hex_rgb(couleur_categorie(categorie, marque))
    accent = hex_rgb(marque["couleur_accent"])
    img = Image.new("RGBA", (l, h), fond + (255,))
    echo(img, l / 2, h / 2 - 120, [220, 330, 440, 550], 8, 0.16)
    d = ImageDraw.Draw(img)
    blanc = (255, 255, 255)
    t = 300
    marque_logo(d, l / 2 - t / 2, h / 2 - 120 - t / 2, t, blanc)
    d.polygon(pentagone(l / 2, h / 2 - 120 + t * 0.04, t * 0.22), fill=accent)
    y = h / 2 + 110
    for texte, nom, taille, couleur in (("Suivez", "InterDisplay-Medium.otf", 48, blanc),
                                        (marque.get("compte", ""), "InterDisplay-Black.otf", 76, blanc),
                                        (marque["accroche"], "InterDisplay-Medium.otf", 38, accent)):
        f = police(nom, taille)
        for l_ in couper(d, texte, f, l - 2 * M):
            d.text(((l - d.textlength(l_, font=f)) / 2, y), l_, font=f, fill=couleur)
            y += int(taille * 1.25)
        y += 14
    chemin.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(chemin, "JPEG", quality=92)
    return chemin


LR, HR = 1080, 1920   # Reel


def image_reel(texte, categorie, date, chemin, marque, premiere=False):
    """Une image du Reel : texte centré dans la zone sûre (hors interface Instagram)."""
    fond = hex_rgb(couleur_categorie(categorie, marque))
    accent = hex_rgb(marque["couleur_accent"])
    img = Image.new("RGBA", (LR, HR), fond + (255,))
    echo(img, LR - 40, HR - 420, [300, 460, 620, 780], 10, 0.20)
    d = ImageDraw.Draw(img)
    blanc = (255, 255, 255)
    # en-tête descendu pour éviter la barre du haut d'Instagram
    marque_logo(d, M - 6, 226, 64, blanc)
    texte_espace(d, (M + 74, 240), marque["nom"].upper(), police("InterDisplay-ExtraBold.otf", 30), blanc, 2)
    f_date = police("InterDisplay-Medium.otf", 28)
    d.text((LR - M - d.textlength(date, font=f_date), 242), date, font=f_date, fill=blanc)
    haut, bas = 420, HR - 520
    if premiere:
        f_cat = police("InterDisplay-Bold.otf", 34)
        cat = categorie.upper()
        w = sum(d.textlength(c, font=f_cat) + 2 for c in cat)
        d.rounded_rectangle([M, haut, M + w + 48, haut + 64], radius=32, fill=blanc)
        texte_espace(d, (M + 24, haut + 12), cat, f_cat, fond, 2)
        haut += 120
    f, lignes, pas = _bloc(d, texte, "InterDisplay-Black.otf", range(136, 54, -4), LR - 2 * M, bas - haut, 1.08)
    y = haut + (bas - haut - len(lignes) * pas) / 2
    for l_ in lignes:
        d.text((M, y), l_, font=f, fill=blanc if not premiere else blanc)
        y += pas
    d.rectangle([M, bas + 30, M + 90, bas + 38], fill=accent)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(chemin, "JPEG", quality=92)
    return chemin
