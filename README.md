# P15 - Analyse du marche de l'emploi et de l'alternance en Data

## Presentation

P15 est un projet d'analyse exploratoire consacré au marché de l'emploi et de
l'alternance dans les métiers de la data.

Le projet cherche à mieux comprendre :

- les tendances des métiers data ;
- les compétences recherchées ;
- les dynamiques de recrutement et d'alternance ;
- les liens entre emploi, formation et insertion professionnelle.

## Approche

Le projet s'appuie sur une démarche reproductible :

1. identifier et documenter les sources de données autorisées ;
2. nettoyer et standardiser les fichiers ;
3. analyser les données avec Python et Pandas ;
4. produire des visualisations exploratoires ;
5. formuler des constats et des pistes de décision.

Les analyses portent notamment sur les intitulés de postes, les compétences,
les périodes, les territoires, les secteurs et les niveaux de qualification.

## Technologies

- Python
- Pandas et NumPy
- Matplotlib
- Jupyter Notebook
- SQLite
- Git et GitHub

## Organisation du travail

Le projet est développé localement et documenté dans ce dépôt GitHub. Les
notebooks, données sources locales, credentials et résultats intermédiaires
ne sont pas publiés. Une copie des marts analytiques consommés par l'application
Streamlit est versionnée sous `streamlit_app/data/processed/marts/` pour
permettre son hébergement public.

Les recherches et décisions méthodologiques sont conservées dans un journal
interne afin d'assurer la traçabilité du projet.

## Preuve de competences

### Veille metier

- analyse des tendances des métiers Data et de l'alternance ;
- identification des besoins en compétences ;
- formulation de questions métiers et d'axes d'analyse.

### Veille technologique

- utilisation de Python pour le traitement de données ;
- exploration de jeux de données avec Pandas ;
- création de visualisations avec Matplotlib ;
- organisation d'un projet analytique avec notebooks et GitHub.

### Tracabilite des preuves

Les travaux, résultats détaillés et éléments de preuve sont conservés dans
l'environnement de travail du projet. Ce dépôt public présente uniquement le
cadre général et les compétences mobilisées.

## Dépôt GitHub

[Consulter le dépôt GitHub](https://github.com/ferialzamoun-afk/P15)

## Statut

Projet en cours de développement.

## Actualisation automatisee de la veille

Le pipeline quotidien utilise l'API France Travail comme source de veille,
reconstruit la base `data/processed/p15_analytics.duckdb`, puis exporte les
marts Parquet lus par Power BI et Streamlit. Les etapes sont executees dans
l'ordre par `scripts/Run-P15Pipeline.ps1`.

### Installation de la tache Windows

Depuis PowerShell, dans le dossier du projet :

```powershell
.\scripts\Install-P15ScheduledTask.ps1 -DailyAt '06:00' -Limit 100
```

La tache lance `scripts/Run-P15Daily.ps1`, conserve un journal dans
`data/logs/p15_daily.log` et ignore une nouvelle execution si une actualisation
est deja en cours. Pour tester manuellement le flux :

```powershell
.\scripts\Run-P15Daily.ps1 -Limit 10
```

Le fichier `.env` doit contenir les quatre variables France Travail requises :
`FRANCE_TRAVAIL_CLIENT_ID`, `FRANCE_TRAVAIL_CLIENT_SECRET`,
`FRANCE_TRAVAIL_SCOPE` et `FRANCE_TRAVAIL_TOKEN_URL`.

Power BI doit pointer vers les fichiers `.parquet` de
`data/processed/marts/`. Streamlit lit le meme dossier et met les donnees en
cache pendant une heure ; apres une actualisation, attendre l'expiration du
cache ou redemarrer la session Streamlit pour obtenir les nouveaux indicateurs.

Pour le tableau detaille des annonces dans Power BI, utiliser
`data/processed/marts/offres_powerbi.parquet`. Ce mart contient une seule
ligne par `id` d'annonce ; les certifications RNCP sont regroupees dans
`numero_fiches_rncp` et `certifications_rncp`. Le fichier
`bridge_offres_certifications_all.parquet` reste reserve aux analyses de
ventilation RNCP et ne doit pas etre utilise comme table principale des
annonces.

### Lancer les outils analytiques

Depuis la racine du projet, installer ou mettre a jour les dependances puis
lancer l'application Streamlit :

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m streamlit run streamlit_app\app.py
```

Dans Power BI Desktop, charger les fichiers Parquet utiles depuis
`data/processed/marts/` avec **Obtenir les données > Parquet**. Après une
exécution réussie du pipeline, utiliser **Actualiser** dans Power BI Desktop.
Le pipeline planifié ne rafraîchit pas lui-même un rapport Power BI Desktop.
