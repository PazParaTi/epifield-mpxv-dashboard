```markdown
# Chaîne automatisée MPXV – Extraction, Analyse, Prévision & Dashboards Interactifs

**Surveillance épidémiologique synthétique du Monkeypox Virus (MPXV)**  
Projet développé pour automatiser le traitement de données issues de Case Report Forms (CRF), générer des données fictives réalistes avec saisonnalité, analyser les tendances, produire des prévisions et déployer des dashboards multi-niveaux (local, national, international).

**Auteur** : Camill Lallement aka PazParaTi  
**Date actuelle** : Février 2026

## Objectifs

- Extraire automatiquement des données structurées depuis des formulaires Word (.docx)
- Générer des données synthétiques réalistes (900 cas sur 2 ans, saisonnalité pluvieuse, modulation régionale)
- Normaliser, enrichir et cataloguer les variables extraites
- Calculer des indicateurs clés : positivité, incidence, sévérité, charge virale, Ct vs délai, mobilité, comorbidités
- Produire des prévisions temporelles (Prophet / Exponential Smoothing)
- Générer des visualisations et dashboards :
  - **Interactif** : Streamlit (public, filtres, Plotly, KPI avec alertes couleur/emoji)
  - **Statique** : HTML/PNG (local, national, international)

## Lien public (déploiement Streamlit Community Cloud)

**Dashboard interactif en ligne** :  
https://PazParaTi-epifield-mpxv-dashboard.streamlit.app

## Architecture actuelle (2026)

```
.
├── main.py                       # Pipeline extraction CRF Word → CSV/JSON
├── dashboard_app.py              # Dashboard interactif Streamlit (déployé public)
├── rdmStats.py                   # Générateur données synthétiques (900 cas, saisonnalité)
├── analyze_extraction.py         # Normalisation, catalogue variables, variables dérivées, plan comparaisons
├── analyse.py                    # Nettoyage final, prévisions, graphs PNG, dashboards HTML statiques
├── requirements.txt              # Dépendances (streamlit, pandas, plotly, etc.)
├── runtime.txt                   # Force Python 3.12 sur Cloud (évite bugs imghdr)
│
├── Script extraction/            # Extraction et parsing Word
│   ├── extract_word.py
│   ├── parsers.py
│   ├── aggregator.py
│   ├── export.py
│   └── ...
│
├── dashboard_outputs/            # Sorties visuelles et agrégées
│   ├── *.png                     # Graphs matplotlib/seaborn
│   ├── data_*.csv                # local / national / international
│   ├── national_forecast.csv     # Prévisions Prophet
│   └── dashboard_*.html          # Versions statiques
│
├── synthetic_outputs/            # Données fictives (rdmStats.py)
│   ├── donnees_synthetiques.json
│   ├── positivite_par_semaine.csv
│   └── ...
│
└── outputs/                      # Catalogues issus de analyze_extraction.py
    ├── variables_catalog.csv
    └── comparison_plan.json
```

## Fonctionnalités principales

- Données synthétiques : 900 cas (2024–2025), sinus saisonnier (pics août), régions (RDC +20 %, Nigeria +10 %, etc.)
- Prévisions incidence/positivité (Prophet avec covariates saison)
- Dashboards Streamlit interactifs :
  - KPI globaux (incidence, positivité, tests/cas, alerte ✅/⚠️/🛑)
  - Tabs : Local (cas individuels), National (tendances/sévérité), International (harmonisé OMS)
  - Graphs Plotly : lignes prévisionnelles, heatmaps saison/région, barres âge/sexe/mobilite
  - Filtres : dates, régions, comorbidités
- Dashboards HTML statiques exportés (fallback offline)
- Catalogue dynamique variables + plan de comparaisons automatique

## Installation & Utilisation locale

```bash
# 1. Clone ou ouvre le dossier
cd "chemin/vers/epifield-mpxv-dashboard"

# 2. Environnement virtuel (recommandé)
python -m venv .venv
# Windows
.\.venv\Scripts\Activate.ps1
# Linux/macOS
source .venv/bin/activate

# 3. Dépendances
pip install -r requirements.txt

# 4. Générer données fictives
python rdmStats.py

# 5. Lancer le dashboard interactif
streamlit run dashboard_app.py
# → http://localhost:8501
```

## Déploiement public (déjà fait)

- Repo GitHub : https://github.com/PazParaTi/epifield-mpxv-dashboard
- Hébergé sur Streamlit Community Cloud
- Python 3.12 (via runtime.txt + Advanced settings)
- Mise à jour automatique : modifie → commit → push → redéploiement en ~2 min

## Commandes utiles (récap)

```bash
# Données synthétiques
python rdmStats.py

# Extraction CRF Word (si dossier word_forms/ présent)
python main.py

# Pré-analyse & catalogue
python analyze_extraction.py

# Analyse complète + graphs + prévisions + HTML
python analyse.py

# Dashboard interactif
streamlit run dashboard_app.py
```

## Prochaines étapes envisagées

- Cartes interactives (Folium/Plotly : heatmaps incidence/région)
- Alertes automatiques (email/SMS sur seuils critiques)
- Export PDF des KPI et graphs
- Mode sombre/clair toggle + accessibilité
- Pipeline CI/CD (GitHub Actions : tests + lint + auto-deploy)
- Intégration Power BI/Tableau via exports CSV automatisés

Projet créé et maintenu par **Camill Lallement aka PazParaTi**  
Février 2026 – Pour l’entraînement, la simulation et la sensibilisation à la surveillance épidémiologique.
```