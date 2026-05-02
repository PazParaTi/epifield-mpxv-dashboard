# Chaîne automatisée d’analyse MPXV — Extraction, Pré‑analyse, Agrégations et Dashboards

## 1. Objectif général
- Automatiser le traitement des données MPXV issues des CRF (Case Report Forms).
- Produire des jeux de données multi‑niveaux (local / national / international) et des dashboards décisionnels destinés aux différents niveaux de pilotage (opérationnel, stratégique, partenaires internationaux).

---

## 2. Architecture du projet (fichiers et dossiers)
Arborescence (extrait) :
- `Script extraction/`  
  - `extract_word.py` — lecture .docx (extraction texte).  
  - `parsers.py` — règles d’extraction des variables depuis le texte CRF.  
  - `aggregator.py` — assembly : appelle les parsers et construit les enregistrements.  
  - `export.py` — fonctions d’export CSV/JSON.  
  - `main.py` — pipeline d’extraction (fichiers Word → extraction.csv / extraction.json).
  - `rdmStats.py` — générateur de données synthétiques (utile pour tests).
- `Script preAnalyse/`  
  - `analyze_extraction.py` — pré‑analyse, normalisation des variables extraites, catalogue de variables.
- `Script Analyse/`  
  - `analyse.py` — nettoyage final, calcul des variables dérivées, création des graphiques et génération des dashboards HTML.
- Sorties et données :
  - `synthetic_outputs/` — exemples / sorties synthétiques (`donnees_synthetiques_flat.csv`, `aperçu_global.csv`, ...).
  - `dashboard_outputs/` — PNG des graphiques, `dashboard.html` (index), et nouveaux fichiers :  
    - `data_local.csv`, `data_national.csv`, `data_international.csv`  
    - `dashboard_local.html`, `dashboard_national.html`, `dashboard_international.html`
- Documentation :
  - `Documentation/note_comparative.txt` — note comparative expliquant les choix analytiques.

Rôle bref des scripts :
- `extract_word.py` + `parsers.py` + `aggregator.py` → extraire et structurer les CRF.
- `analyze_extraction.py` → pré‑analyse, catalogue de variables et normalisation.
- `rdmStats.py` → génération de jeu de données synthétiques pour tests.
- `analyse.py` → nettoyage, dérivés, graphiques, agrégations multi‑niveaux et dashboards.

---

## 3. Flux de données (Data Pipeline)
Étapes globales :
1. Extraction (Word → enregistrements structurés)  
2. Pré‑analyse (normalisation, booléens, dates)  
3. Dérivations (variables cliniques et d’exposition)  
4. Agrégations multi‑niveaux (local / national / international)  
5. Génération de graphiques (PNG)  
6. Assemblage de dashboards HTML (index + 3 déclinaisons)

Diagramme Mermaid (texte) :

```mermaid
flowchart LR
  A[CRF (.docx)] --> B[extract_word.py]
  B --> C[parsers.py / aggregator.py]
  C --> D[extraction.csv / extraction.json]
  D --> E[analyze_extraction.py (pré‑analyse)]
  E --> F[analyse.py (dérivations / agrégations)]
  F --> G[graphes PNG -> dashboard_outputs/]
  F --> H[data_local.csv, data_national.csv, data_international.csv]
  G --> I[dashboard_local.html]
  G --> J[dashboard_national.html]
  G --> K[dashboard_international.html]
```

---

## 4. Installation

Prérequis recommandés
- Python 3.8+ (3.11 testé).
- Environnement virtuel recommandé (`venv`).

Exemple d’installation (Windows / PowerShell) :

```powershell
# Créer et activer un virtualenv
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Installer dépendances principales
pip install --upgrade pip
pip install pandas numpy matplotlib seaborn python-dateutil python-docx
```

Packages utiles (liste non exhaustive) :
- pandas, numpy, matplotlib, seaborn, python-dateutil, python-docx

---

## 5. Utilisation

Préparation
- Placez vos fichiers `.docx` (CRF) dans le dossier attendu (`Script extraction/word_forms` si utilisé).
- Si vous testez sans CRF réels, exécutez `rdmStats.py` pour générer `synthetic_outputs/donnees_synthetiques_flat.csv`.

Exécution des étapes
- Extraction (depuis `Script extraction/`) :

```powershell
cd "Script extraction"
python main.py
# -> génère extraction.csv et extraction.json
```

- Pré‑analyse (si utilisé séparément) :

```powershell
# depuis le projet, ex :
python .venv\Scripts\Script\ preAnalyse\analyze_extraction.py
```

- Analyse, dérivés et dashboards :

```powershell
# depuis le projet (le script se positionne correctement vers Script extraction)
python .venv\Scripts\Script\ Analyse\analyse.py
# ou, depuis Script Analyse :
cd "Script Analyse"
python analyse.py
```

Sorties (emplacement)
- Graphiques PNG et dashboards HTML : `Script extraction/dashboard_outputs/`
  - `dashboard_outputs/dashboard.html` (index global)
  - `dashboard_outputs/dashboard_local.html`
  - `dashboard_outputs/dashboard_national.html`
  - `dashboard_outputs/dashboard_international.html`
- Jeux de données agrégés :
  - `dashboard_outputs/data_local.csv`
  - `dashboard_outputs/data_national.csv`
  - `dashboard_outputs/data_international.csv`

Ouvrir dashboards : double‑clic sur les fichiers HTML ou ouvrir dans un navigateur.

---

## 6. Dérivations et enrichissements automatiques
Le pipeline calcule plusieurs variables dérivées utiles pour analyses et reporting :

- `pcr_any_positif` : booléen indiquant si le patient a au moins un prélèvement PCR positif (lésion ou oropharynx).
- `ct_value_num` : valeur Ct consolidée (prend la valeur pertinente entre lésion et oropharynx).
- `charge_virale_cat` : catégorie de charge virale dérivée de `ct_value_num` (ex. `haute`, `moyenne`, `basse`).
- `nb_symptomes` : somme des indicateurs binaires de symptômes (proxy charge symptomatique).
- `severe` : booléen heuristique indicateur de sévérité clinique (composite : nombre de symptômes, comorbidités, étendue lésions).
- `vih_statut` : statut VIH condensé (suppressé / non_suppressé / sans_ARV / négatif/inconnu).
- `nb_localisations_lesions` : nombre de sites lésionnels (compte les items séparés par `;`).
- `delai_symptomes_vers_pcr_jours` : délai entre début symptômes et date PCR (jours).
- `mobilite_groupe` / flags d’exposition : variables combinées (antécédent voyage, zone épidémie, contact cas) pour catégoriser l’exposition.

Ces dérivations sont conçues pour être robustes aux valeurs manquantes et utilisables en agrégats.

---

## 7. Datasets multi‑niveaux (output)
- `data_local.csv`  
  - Granularité : une ligne = un cas (données individuelles)  
  - Contenu : toutes les variables dérivées utiles en contexte opérationnel (symptômes détaillés, Ct, localisations, flags voyage/contact, mobilité, etc.)  
  - Usage : pilotage local, investigation de cas, contact tracing.

- `data_national.csv`  
  - Granularité : agrégation par `semaine` / `sexe` / `age_bin`  
  - Indicateurs : `total_cases`, `positivity_rate`, `median_ct`, `mean_nb_symptomes`, `proportion_severe`, distribution `charge_virale_*`  
  - Usage : suivi épidémiologique national, décisions stratégiques, allocation de ressources.

- `data_international.csv`  
  - Granularité : agrégats harmonisés (semaine, grands groupes d’âge, sexe)  
  - Indicateurs standardisés : `total_cases`, `positivity_rate`, `severe_rate`, `travel_related_rate`, `median_ct` (optionnel)  
  - Usage : reporting OMS/ECDC, comparaisons inter‑pays, échanges de signalements.

---

## 8. Dashboards multi‑niveaux (contenu et public cible)
- `dashboard_local.html` (Public : équipes locales / unités de santé)  
  Contenu : graphiques opérationnels — incidence & positivité hebdomadaire, Ct vs délai, nombre symptômes par statut PCR, distribution des localisations, mobilité/exposition.  
  Objectif : identification rapide de cas sévères/clusters et actions terrain.

- `dashboard_national.html` (Public : autorités sanitaires nationales)  
  Contenu : tendances par semaine, positivité, sévérité par groupes (VIH, âge), effet vaccinal, indicateurs d’hospitalisation potentielle.  
  Objectif : pilotage stratégique et allocation de ressources.

- `dashboard_international.html` (Public : partenaires internationaux — OMS / ECDC)  
  Contenu : indicateurs harmonisés et synthétiques (incidence agrégée, taux de positivité, proportion sévère, proportion liée aux voyages, distribution par grands groupes d’âge).  
  Objectif : comparabilité, interopérabilité, signalement de signaux épidémiques.

---

## 9. Note comparative
Une note comparative détaillée est disponible dans `Documentation/note_comparative.txt` — elle explicite les choix de variables, les principes d’agrégation et les justifications par niveau décisionnel.

---

## 10. Limites connues
- Sensibilité forte à la qualité et à l’exhaustivité des données sources (CRF).  
- Dates manquantes ou mal formatées impactent calcul des délais et des semaines épidémiologiques.  
- Valeurs Ct souvent incomplètes ⇒ `median_ct` peut être manquant pour certains groupes.  
- Risque de biais si la couverture des tests n’est pas homogène dans le temps ou l’espace.  
- Données sensibles (VIH, identifiants) nécessitent gouvernance et contrôles d’accès stricts.

---

## 11. Améliorations futures (suggestions)
- API REST pour accès programmatique aux datasets agrégés.  
- Détection automatique d’anomalies (changements abrupts de positivité, pics inhabituels).  
- Dashboard interactif (Plotly Dash / Streamlit / PowerBI) avec filtres géographiques et temporels.  
- Intégration de tableaux de bord métier (PowerBI / Tableau) via exports réguliers.  
- Surveillance en quasi‑temps réel et alerting (seuils paramétrables).  
- Tests automatisés et pipeline CI pour garantir reproductibilité.

---

## 12. Licence
- Placeholder : spécifiez ici la licence souhaitée (ex. MIT, GPL‑3.0, CC‑BY).  
  Exemple à insérer : `MIT License` ou autre, selon politique de votre institution.

---

## 13. Annexes — commandes utiles

Activer virtualenv (PowerShell) :
```powershell
.\.venv\Scripts\Activate.ps1
```

Installation dépendances :
```powershell
pip install pandas numpy matplotlib seaborn python-dateutil python-docx
```

Exécution rapide (analyse complète) :
```powershell
# Générer données synthétiques (optionnel)
python Script\ extraction\rdmStats.py

# Lancer l'analyse et générer dashboards
python ".venv\Scripts\Script Analyse\analyse.py"
```

Fichiers de sortie principaux :
- `Script extraction/dashboard_outputs/*.png`
- `Script extraction/dashboard_outputs/dashboard.html`
- `Script extraction/dashboard_outputs/dashboard_local.html`
- `Script extraction/dashboard_outputs/dashboard_national.html`
- `Script extraction/dashboard_outputs/dashboard_international.html`
- `Script extraction/dashboard_outputs/data_local.csv`
- `Script extraction/dashboard_outputs/data_national.csv`
- `Script extraction/dashboard_outputs/data_international.csv`

---

Si vous le souhaitez, je peux générer une version anglaise ou préparer un commit Git contenant ce fichier.
