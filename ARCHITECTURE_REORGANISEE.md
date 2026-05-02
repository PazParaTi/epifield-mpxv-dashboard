# Architecture reorganisee Epifield

Cette arborescence suit le schema Mermaid du projet :

- `sources_donnees/` : CRF Word et generateur synthetique `rdmStats.py`.
- `selection_mode/` : exemple de configuration `DATA_MODE`.
- `ingestion/` : extraction Word, parsing, aggregation et export vers `donnees/reelles/`.
- `donnees/` : donnees reelles et synthetiques.
- `traitement/` : normalisation, catalogue de variables, analyse et previsions.
- `sorties_intermediaires/` : datasets local, national, international, regional et previsions.
- `presentation/` : application Streamlit et dashboards statiques.
- `documentation/` : schemas, livrables, notes et flux de data.
- `infrastructure/` : environnement local et historique Git archive.
- `archives/` : zips, anciens scripts et fichiers bureautiques.
