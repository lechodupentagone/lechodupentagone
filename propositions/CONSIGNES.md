# Propositions du matin — consignes de rédaction

Chaque matin, Claude prépare 3 à 5 sujets pour L'Écho du Pentagone. L’éditeur poste lui-même sur Instagram et Facebook et publie les articles sur le site en cochant « publier » dans la Google Sheet.

## Matière première
1. `data/veille.json` : éléments collectés automatiquement sur 7 jours (presse, actes municipaux avec lien PDF).
2. La recherche web du jour : La Roche-sur-Yon, Agglo, Vendée. Pour chaque sujet retenu, lire les articles sources.
3. Écarter ce qui figure dans les `propositions/*/brouillon.json` des 7 derniers jours, sauf fait nouveau.

## Choix des sujets
- Priorité à ce qui touche le quotidien des Yonnais et des Vendéens : décisions municipales et de l'Agglo, travaux, transports, écoles, commerces, sécurité, sport et culture locaux.
- Les actes municipaux non délibérés (décisions du maire, arrêtés) sont un angle propre au média. Expliquer ce qu'ils changent concrètement, en citant le numéro de l'acte.
- Mélanger les catégories. Au moins un sujet « positif » ou pratique par jour.

## Règles de rédaction
- Écrire avec nos propres mots. Ne jamais reproduire de phrase d'un article de presse (droit voisin), ni de photo. Citer et lier chaque source.
- N'écrire que des faits vérifiés dans les sources : dates, montants, noms. Sinon, ne pas l'écrire. Pas d'extrapolation.
- Ton neutre et factuel. Le média « parle à tout le monde » : pas d'opinion, pas d'adjectifs de jugement, pas de prise de parti politique. Les positions des élus et des groupes sont rapportées comme telles, avec leur auteur.
- Faits divers : pas de nom de victime ni de mis en cause non public, pas de détail sordide, présomption d'innocence.
- Le gentilé est « Yonnais » (jamais « Rochelais »).

## Formats (champ du brouillon)
- `categorie` : rubrique principale (sa couleur habille les visuels). `autres_rubriques` (facultatif) : liste des rubriques où l'article doit aussi apparaître, par exemple un sujet de l'Agglo qui touche aussi l'Économie.
- `titre` : 60 à 110 caractères, informatif, sans point d'exclamation.
- `article` : 250 à 600 mots en Markdown. Un chapeau en gras, puis les faits, le contexte, et « ce qui va se passer ».
- `legende_instagram` : 400 à 900 caractères. Une accroche, 3 à 5 phrases, « Lien en bio », puis 5 à 8 hashtags (#LaRocheSurYon #Vendée …).
- `texte_facebook` : 400 à 1 000 caractères, plus développé. Terminer par « Source : … ».
- `carrousel` : 3 à 5 diapos `{titre ≤ 40 caractères, texte ≤ 220 caractères}`. La couverture et la diapo finale sont ajoutées automatiquement.
- `reel` : 4 à 7 phrases de 3 à 12 mots. La première accroche, la dernière conclut.

## Fabrication
1. Écrire `propositions/AAAA-MM-JJ/brouillon.json` (liste de sujets, voir l'en-tête de `scripts/propositions.py`).
2. `pip install -r requirements.txt --break-system-packages -q`
3. `python scripts/propositions.py propositions/AAAA-MM-JJ/brouillon.json`
4. Commit et push sur `main`. La prochaine collecte importe les articles dans la Sheet.
5. Publier la page `propositions/AAAA-MM-JJ/index.html` et ses fichiers comme artifact. Republier l'artifact dont le slug figure dans `propositions/ARTIFACT.txt`, en mode replace, pour garder le même lien.
