# 🏥 EpiField – Architecture Technique [Quick Reference]

## Pipeline de Haut Niveau

```
┌─────────────────────────────────────────────────────────────┐
│                   SOURCES DE DONNÉES                        │
│  CRF Word (réelles)  |  rdmStats.py (synthétiques)         │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│               🔀 SELECTEUR MODE (env var)                   │
│  DATA_MODE = "real"  |  DATA_MODE = "synthetic"            │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│              COUCHE 1 : EXTRACTION                          │
│  extract_word.py → parsers.py → aggregator.py → export.py │
│  Output: extraction.csv + extraction.json                   │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│          COUCHE 2 : TRAITEMENT & ENRICHISSEMENT             │
│  analyze_extraction.py → variables_catalog.csv              │
│  analyse.py → data_local/national/international.csv         │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│           COUCHE 3 : PRÉSENTATION & DÉPLOIEMENT             │
│  dashboard_app.py (Streamlit) → Streamlit Cloud             │
│  ✨ KPI | 📊 14+ Graphs | 🔍 Filtres | 📄 Exports          │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                    UTILISATEURS                             │
│  👨‍⚕️ Épidémiologistes | 👨‍💼 Gestionnaires | 🔬 Scientifiques │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔑 Briques Techniques Principales

| Brique | Responsabilité | Technologie | Entrée | Sortie |
|--------|---|---|---|---|
| **Extraction** | Parser CRF Word → données structurées | `python-docx` + regex | Fichiers .docx | CSV/JSON |
| **Normalisation** | Classification variables + catalogue | pandas + Python | CSV brut | Variables_catalog.csv |
| **Analyse** | Nettoyage + prévisions + agrégations | pandas + Prophet | JSON brut | 3 niveaux (local/nat/intl) |
| **Dashboard** | Interface interactive temps-réel | Streamlit + Plotly | CSV multi-niveaux | HTML/Web public |
| **Déploiement** | Git → Cloud | GitHub + Streamlit | Code + Data | URL publique 24/7 |

---

## 🌊 Flux de Données – Exemple MPXV

```
Cas clinique → CRF Word → extract_word.py
    ↓
[Parse : démo, symptômes, PCR, vaccin, VIH]
    ↓
100+ variables structurées → aggregator.py
    ↓
JSON avec traçabilité source
    ↓
analyze_extraction.py : classi…fication auto
    ├─ Quantitatives (âge, CT, délai)
    ├─ Nominales (région, lesions, pathogène)
    ├─ Binaires (vaccin, sévérité, PCR+)
    └─ Temporelles (semaine, date PCR)
    ↓
analyse.py : nettoyage + Prophet + agrégations
    ├─ data_local.csv (1500 cas, détail)
    ├─ data_national.csv (régions, n=1500)
    ├─ data_international.csv (pays, n=5)
    └─ national_forecast.csv (12 sem, confiance)
    ↓
dashboard_app.py : Streamlit
    ├─ Filtre région/semaine/pathogène
    ├─ 14 graphiques interactifs Plotly
    ├─ KPI avec alertes (codes couleur + 😷😷😷)
    └─ Exports CSV/PNG pour rapports
    ↓
Streamlit Cloud public
    ├─ URL: https://PazParaTi-epifield-mpxv-dashboard.streamlit.app
    ├─ Temps réel (rafraîch ~30s)
    └─ Utilisateurs web
```

---

## 💚 Switch Synthétique ↔ Réel – Explication Simple

### Contexte Pourquoi ?
- **Développement** : Pas d'accès CRF réels (données sensibles)
- **Tests** : Besoin de données réalistes pour valider pipeline
- **Démo** : Montrer plateforme sans révéler données patients
- **Prod sécurisée** : Deux environnements strictement séparés

### Implémentation
```python
# dashboard_app.py ligne ~50
MODE = os.getenv("DATA_MODE", "synthetic")

if MODE == "synthetic":
    # Changer 2 lignes pour activer synthétique
    data = rdmStats.generate_synthetic_data()  # 900 cas fictifs
    print("🔄 Mode SYNTHÉTIQUE activé (développement)")
else:
    # Changer 2 lignes pour passer au réel
    data = pd.read_json("extraction_real.json")  # Vraies données
    print("🚨 Mode RÉEL activé (production)")
```

### Déploiement
- **Local** : `export DATA_MODE=synthetic` → Développeurs testent
- **Prod Streamlit** : `export DATA_MODE=real` (secret GitHub) → Utilisateurs finaux
- **Branch git** : Deux fichiers `.json` versionnés (anonymisés)

---

## 🏗️ Infrastructure – Architecture Cloud

```
GitHub Repository                    Streamlit Community Cloud
┌──────────────────┐                 ┌────────────────────────┐
│ Code Python      │ git push        │ Python 3.12 Runtime    │
│ + Données        │ ──────────────→ │ + Cache intégré         │
│ + requirements   │                 │                        │
│ + secrets        │                 │ Auto-redéploiement     │
└──────────────────┘                 │ à chaque push           │
                                     └────────────────────────┘
                                              ↓
                                     https://epifield-...
                                     .streamlit.app
                                              ↓
                                        Web Public 24/7
```

### Avantages
- ✅ **Gratuit** (GitHub + Streamlit Community)
- ✅ **Serverless** (pas de serveur à gérer)
- ✅ **Scalable** (auto-scaling inclus)
- ✅ **Sécurisé** (HTTPS, secrets GitHub)
- ✅ **Rapide** (déploiement 2-5 min après push)

### Limites (respectées)
- ⚠️ 1 Go RAM = ~10k cas max (EpiField: 1500 ok ✓)
- ⚠️ Rafraîchissement ~30s (acceptable pour surveillance épidémio)
- ⚠️ 1 instance = pas de concurrence massive (futur: PG)

---

## 📈 Prévisions – Comment Ça Marche ?

```
Données nationales (100 semaines passées)
           ↓
[Prophet.fit()] ← Modèle temporel Facebook
           ↓
Détection :
  - Tendance (croissance? déclin?)
  - Saisonnalité (cycles pluviaux → pics MPXV)
  - Changepoints (alertes naturelles)
           ↓
Prévisions 12 semaines + confiance 80%/90%
           ↓
national_forecast.csv
           ↓
Dashboard: Zone grise = intervalle confiance
```

---

## 🎨 Dashboard – Ce Qu'on Voit

```
┌─── Titre: MPXV Dashboard (Interactive) ───────────────┐
│                                                        │
│  [Filtre Région] [Filtre Semaine] [Filtre Pathogène]  │
│                                                        │
│  ┌─────────────────────────────────────────────────┐  │
│  │ KPI Cards (couleur dynamique)                    │  │
│  │ ✅ 1500 cas | 😷😷😷 68% sévérité | 📈 +15% trend  │
│  └─────────────────────────────────────────────────┘  │
│                                                        │
│  ┌─────────────────────────────────────────────────┐  │
│  │ Graphique 1: Incidence par semaine (ligne)      │  │
│  │ Graphique 2: Positivité heatmap (région/semaine)   │
│  │ Graphique 3: Prévision Prophet 12 sem (zone grise) │
│  │ Graphique 4-14: Autres analyses...               │  │
│  └─────────────────────────────────────────────────┘  │
│                                                        │
│  💾 Export CSV | 📸 Capturer PNG | 🌐 Partager      │
│                                                        │
└────────────────────────────────────────────────────────┘
```

---

## 📊 Fichiers Clés – Checkliste Rapide

| Fichier | Type | Rôle | Mis à jour |
|---------|------|------|-----------|
| `main.py` | Script | Extraction CRF | Manuel (push fichiers) |
| `dashboard_app.py` | App | Interface web | Auto (Streamlit Cloud) |
| `rdmStats.py` | Script | Données synthétiques | Test/démo |
| `analyze_extraction.py` | Script | Catalogue variables | Auto (pipeline) |
| `analyse.py` | Script | Prévisions + agrégations | Auto (pipeline) |
| `extraction.json` | Data | CRF brut | Manuel |
| `data_local.csv` | Data | Cas détail | Auto (pipeline) |
| `data_national.csv` | Data | Agrégations nationales | Auto (pipeline) |
| `dashboard_outputs/` | Dossier | Résultats finaux | Auto (pipeline) |

---

## 🚀 Mise en Production – 5 Étapes

1. **Push GitHub**
   ```bash
   git add .
   git commit -m "Extraction MPXV v2.0"
   git push origin main
   ```

2. **Déclenche automatiquement Streamlit**
   - GitHub détecte push
   - Streamlit re-build l'app

3. **Exécute les scripts (backend)**
   - Python charge le repo
   - `main.py` → extraction CRF
   - `analyse.py` → prévisions + agrégations

4. **Met à jour les données**
   - CSV rechargés en cache Streamlit
   - KPI recalculés

5. **App reste public**
   - URL toujours accessible
   - Nouveaux filtres/graphiques immédiatement visibles
   - Prévisions à jour

**Temps total** : ~3-5 minutes ⏱️

---

## 🎓 Glossaire

- **CRF** = Case Report Form (formulaire médical)
- **CSV** = Comma-Separated Values (Excel-compatible)
- **JSON** = JavaScript Object Notation (structured data)
- **Streamlit** = Python framework dashboards (fast prototyping)
- **Plotly** = Interactive graph library (zoom, hover, export)
- **Prophet** = Facebook forecasting library (time-series)
- **Regex** = Regular expressions (pattern matching text)
- **Cache** = Stockage rapide données (améliore performance)

---

## 🔗 Ressources

- **Dashboard Live** : https://PazParaTi-epifield-mpxv-dashboard.streamlit.app
- **Code GitHub** : [Lien privé EpiField]
- **Documentation** : `/Epifield/Documentation/README.md`
- **Contact** : Équipe EpiField

---

**Affichage recommandé** : A3 (poster équipe développement)  
**Imprimer** : Format couleur pour codes couleur clairs  
**Mise à jour** : Tous les 3 mois ou selon évolutions archi

---

*Version 1.0 – Architecture Technique EpiField – Avril 2026*
