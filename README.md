# L'Écho du Pentagone — collecte, validation, publication

Chaîne entièrement gratuite :

```
Flux RSS + actes municipaux ──► Google Sheet « File de validation » ──► vous cochez « publier »
        (GitHub Actions, toutes les 2 h)                                      │
                                                                              ▼
              Site (GitHub Pages)  ◄──  visuel + article générés  ──►  Facebook + Instagram
                                  (GitHub Actions, toutes les 30 min)
```

| Brique | Outil | Coût |
|---|---|---|
| Automatisation | GitHub Actions (dépôt **public**) | 0 € |
| Site | GitHub Pages | 0 € (nom de domaine facultatif : ~10 €/an) |
| File de validation | Google Sheet + compte de service Google | 0 € |
| Publication | API Meta (page Facebook + compte Instagram pro) | 0 € |

Le dépôt doit être **public** : les minutes GitHub Actions y sont illimitées (2 000 min/mois en privé, insuffisant). Les mots de passe et jetons restent privés dans les « Secrets » du dépôt.

---

## 1. Choisir le nom et réserver les comptes

1. Réservez **@lechodupentagone** sur Instagram (et @echodupentagone par précaution), et lechodupentagone.fr si vous voulez un domaine.
2. Créez la **page Facebook** « L'Écho du Pentagone », nom d'utilisateur `lechodupentagone` (depuis votre profil : Pages › Créer une page). Photo de profil : `site/assets/identite/logo.png` ; couverture : `site/assets/identite/couverture-facebook.png`.
3. Créez le **compte Instagram**, passez-le en compte **professionnel** (Paramètres › Type de compte), puis reliez-le à la page Facebook (dans les paramètres de la page : Comptes liés › Instagram).

## 2. GitHub : dépôt et site

1. Créez un compte sur github.com, puis un dépôt **public** (ex. `yon-info`).
2. Envoyez-y tout le contenu de ce dossier (bouton « Add file › Upload files », en gardant les sous-dossiers, y compris `.github`).
3. Dans le dépôt : **Settings › Pages › Source : GitHub Actions**.
4. Modifiez dans GitHub (icône crayon) :
   - `config.yaml` : bloc `marque` (déjà réglé pour L'Écho du Pentagone ; `site_url` = `https://VOTRE-COMPTE.github.io/VOTRE-DEPOT`, directeur de publication, contact) ;
   - `site/_config.yml` : `title`, `description`, `url`, `baseurl` (`/VOTRE-DEPOT`), liens Facebook et Instagram ;
   - `site/mentions-legales.md` : vos nom et adresse de contact.

## 3. Google : la file de validation

1. Créez une Google Sheet vide (ex. « Média — file de validation »). Son **identifiant** est la partie de l'adresse entre `/d/` et `/edit`.
2. Allez sur console.cloud.google.com › créez un projet › **API et services › Bibliothèque** › activez **Google Sheets API**.
3. **API et services › Identifiants › Créer des identifiants › Compte de service**. Ouvrez-le › onglet **Clés** › Ajouter une clé › JSON : un fichier se télécharge.
4. Partagez la Google Sheet avec l'adresse e-mail du compte de service (`…@….iam.gserviceaccount.com`), droit **Éditeur**.
5. Dans le dépôt GitHub : **Settings › Secrets and variables › Actions › New repository secret** :
   - `GOOGLE_SERVICE_ACCOUNT_JSON` : tout le contenu du fichier JSON ;
   - `SHEET_ID` : l'identifiant de la Google Sheet.

Après la première collecte, l'onglet « File de validation » apparaît. Sélectionnez la colonne **J (publier)** › Insertion › **Case à cocher**.

## 4. Meta : publication Facebook et Instagram

1. Sur developers.facebook.com, créez une **application** (type « Entreprise »). Elle peut rester en mode développement : vous publiez uniquement sur vos propres comptes, sans revue de Meta.
2. Ouvrez l'**Explorateur de l'API Graph** (Outils), choisissez votre application, puis « Générer un jeton d'accès » avec les autorisations : `pages_show_list`, `pages_read_engagement`, `pages_manage_posts`, `instagram_basic`, `instagram_content_publish`, `business_management`.
3. Transformez ce jeton en jeton longue durée (Outils › **Débogueur de jeton d'accès** › « Prolonger le jeton d'accès »).
4. Avec ce jeton, dans l'explorateur, appelez `me/accounts` : récupérez l'`id` de la page et son `access_token` (jeton de page, sans expiration tant que vous ne changez pas de mot de passe).
5. Appelez `ID_DE_LA_PAGE?fields=instagram_business_account` : récupérez l'`id` Instagram.
6. Ajoutez les secrets GitHub : `META_PAGE_ID`, `META_PAGE_TOKEN`, `IG_USER_ID`.

Sans ces trois secrets, la chaîne fonctionne quand même : le site est publié, les réseaux sont simplement sautés.

## 5. Premier essai

1. Onglet **Actions** du dépôt › **Collecte** › *Run workflow*. Au bout d'une minute, la Google Sheet se remplit. Le journal indique les sources en erreur : désactivez-les dans `config.yaml` (mettre `#` devant les lignes).
2. Dans la Google Sheet, sur une ligne : réécrivez si besoin le **titre** (il sert pour le visuel et l'article), rédigez le **texte à publier**, cochez **publier**.
3. **Actions › Publication › Run workflow**. Le statut passe à « en ligne (site) » puis « publié », avec les liens Facebook et Instagram.

Ensuite tout tourne seul : collecte toutes les 2 h, publication toutes les 30 min de ce que vous avez coché.

## Au quotidien

- Ouvrez la Google Sheet (aussi sur téléphone), triez par « collecté le ».
- Pour chaque élément retenu : titre propre, texte à publier, case cochée. Le reste : laissez la case vide.
- Les PDF des actes retenus sont archivés dans `archives/actes/` (le portail de la Ville retire ses actes au bout de deux mois).

## Ajouter une info à la main (Facebook, Instagram, terrain…)

Les comptes Facebook et Instagram des autres ne peuvent pas être lus automatiquement (Meta l'interdit sans autorisation spéciale). Pour publier une info vue sur un réseau social, ou apprise sur le terrain, ajoutez une ligne dans la Google Sheet, y compris depuis l'application mobile :

- **source** : ex. « Page Facebook de la Ville » ;
- **catégorie** : Municipal, Agglo, Vendée… (elle donne la couleur du visuel) ;
- **titre** : le titre du visuel ;
- **lien** : l'adresse de la publication d'origine ;
- **texte à publier** : votre texte ;
- **publier** : cochez. Laissez **statut** vide.

La publication suivante la traite comme les autres.

## Règles éditoriales (à respecter, c'est vous le directeur de publication)

- **Presse** : jamais de reprise d'article ni de photo. Titre et texte réécrits par vous, lien vers la source (droit voisin des éditeurs de presse, loi n° 2019-775).
- **Actes** : décrire l'acte (objet, montant, date, numéro) et renvoyer vers le PDF officiel.
- **Neutralité** : une marque présentée comme média d'information doit traiter la majorité et l'opposition avec les mêmes critères, sinon elle sera contestée au premier écart.
- **Droit de réponse** : l'adresse de contact des mentions légales doit être relevée.

## Fichiers

| Fichier | Rôle |
|---|---|
| `config.yaml` | Marque, sources, mots-clés des actes |
| `scripts/collect.py` | Collecte, filtrage, dédoublonnage, écriture dans la Sheet |
| `scripts/publish.py` | Visuel + article (`preparer`), Facebook + Instagram (`reseaux`) |
| `scripts/visual.py` | Modèle de visuel 1080 × 1350 (couleurs dans `config.yaml`) |
| `site/` | Site Jekyll publié par GitHub Pages |
| `.github/workflows/` | Planification (collecte, publication) |
| `data/vus.json` | Éléments déjà vus (évite les doublons) |

Tester un visuel sur votre ordinateur : `pip install -r requirements.txt` puis `python scripts/publish.py essai "Mon titre" "Municipal" "Source"` (crée `essai.jpg`).
