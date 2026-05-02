# LIVRABLES – Architecture Technique EpiField
## Plateforme de Données en Santé Publique

**Commanditaire** : Chef de projet EpiField  
**Date** : Avril 2026  
**Contexte** : Prototype MPXV | Ambition multi-pathogènes  
**Auteur** : Architecture IT  

---

## 📦 Contenu du Livrable

Ce dossier contient les deux composantes demandées :

### 1️⃣ **SCHEMA_ARCHITECTURE.mmd** – Maquette Technique Dynamique
- **Format** : Mermaid Flowchart (compatible GitHub, VS Code, Confluence, etc.)
- **Lisibilité** : Légendes colorées, code en français, structure claire
- **Couvrage** : Sources de données → Pipeline traitement → Déploiement → Utilisateurs
- **Focus clé** : **Switch synthétique ↔ réel** bien mis en avant (losange décisionnel central)

**Comment visualiser :**
- Copier le contenu `.mmd` dans [Mermaid Live Editor](https://mermaid.live)
- Ou importer dans GitHub / VS Code / Notion / Confluence
- Export PNG/SVG possible pour présentations

---

### 2️⃣ **ARCHITECTURE_TECHNIQUE.md** – Note Explicative Professionnelle
- **Longueur** : 2 pages (selon format standard A4)
- **Langue** : Français fluide et professionnel
- **Structure** :
  1. Vue d'ensemble de l'architecture
  2. Architecture détaillée (3 couches : Ingestion, Traitement, Présentation)
  3. Infrastructure et déploiement (diagramme cloud simplifié)
  4. Switch synthétique ↔ réel (explication du mode de sélection)
  5. Avantages et tableau comparatif
  6. Roadmap d'évolution court/moyen/long terme
  7. Conclusion

---

## 🎯 Principes Directeurs Appliqués

✅ **Architecture simple, sans complexité excessive**  
→ Pipeline linéaire en 3 couches, pas d'orchestrateur Airflow/Kubernetes

✅ **Maquette dynamique et schéma clair**  
→ Flowchart Mermaid avec code couleurs et symboles visuels

✅ **Briques techniques et leur articulation**  
→ Chaque script (extract_word, analyse.py, dashboard_app) positionné dans le flux

✅ **Note explicative courte (1-2 pages)**  
→ Respect de la limite avec structure complète et traçable

✅ **Style fluide et professionnel en français**  
→ Langage adapté aux décideurs IT et épidémiologistes

✅ **Environnement Python + Streamlit**  
→ Stack techno respectée et détaillée

✅ **Low-cost : Streamlit Cloud + GitHub**  
→ 0€ d'infrastructure, pas de Docker

✅ **Multi-pathogènes**  
→ Parseurs et pipeline généralisables

✅ **Temps réel**  
→ Rafraîchissement < 5 min après push GitHub

---

## 🔑 Points Clés de l'Architecture

| Point | Détail |
|-------|--------|
| **Source données** | CRF Word (réelles) OU rdmStats.py (synthétiques) |
| **Sélection mode** | Variable d'environnement `DATA_MODE` |
| **Pipeline extraction** | `extract_word.py` → `parsers.py` → `aggregator.py` → `export.py` |
| **Enrichissement** | `analyze_extraction.py` (classification + variables dérivées) |
| **Analyse** | `analyse.py` (prévisions Prophet, agrégations multi-niveaux) |
| **Présentation** | `dashboard_app.py` (Streamlit interactif) + exports HTML/PNG |
| **Déploiement** | GitHub → Streamlit Cloud (auto-trigger) |
| **Utilisateurs** | Épidémiologistes, gestionnaires, scientifiques |

---

## 📊 Flux Simplifié (Vue haute niveau)

```
CRF Word / rdmStats.py
        ↓
    [SELECTEUR MODE]
        ↓
  EXTRACTION → TRAITEMENT → ENRICHISSEMENT → DASHBOARD STREAMLIT
        ↓                                          ↓
   CSV/JSON                                    Utilisateurs
```

---

## 💡 Utilisation de ce Livrable

### Pour le chef de projet :
1. Présenter le **schéma Mermaid** en réunion de gouvernance IT
2. Distribuer la **note architecture** aux décideurs techniques
3. Valider le scope et l'effort d'implémentation (estimé : 3-4 semaines)

### Pour l'équipe de développement :
1. Utiliser le schéma comme **specification visuelle** du découpage des tâches
2. Consulter la note pour les **critères de qualité** (scalabilité, sécurité, coût)
3. Adapter les scripts existants selon l'architecture proposée

### Pour l'infrastructure :
1. Valider la configuration Streamlit Cloud (ressources, domaine)
2. Mettre en place les **secrets GitHub** (API keys, auth)
3. Configurer le **CD pipeline** (auto-redéploiement sur push)

---

## 🚀 Prochaines Étapes Recommandées

1. **Validation architecture** (2-3 jours)
   - Réunion d'alignement avec équipe IT
   - Ajustements selon feedback métier

2. **Découpage des tâches** (1 jour)
   - Mapping architecture → sprints développement
   - Estimation effort par couche

3. **Implémentation Phase 1** (3-4 semaines)
   - Stabilisation extraction CRF
   - Déploiement dashboard sur Streamlit Cloud
   - Mise en place des données synthétiques (fallback)

4. **Validation + Ajustements** (1-2 semaines)
   - Tests avec utilisateurs finaux
   - Optimisations performance
   - Documentation opérationnelle

5. **Extensibilité multi-pathogènes** (2-3 mois)
   - Analyse nouvelles pathogènes
   - Généralisation parseurs
   - Scalabilité base de données

---

## 📞 Contacts et Questions

- **Architecture** : À adapter selon contexte projet
- **Infrastructure** : Équipe DevOps + Streamlit
- **Métier** : Épidémiologistes et responsables CRF

---

**Version** : 1.0  
**Statut** : ✅ Livrable complet  
**Date dernière mise à jour** : Avril 2026  

---

## Annexes

### A. Lexique Technique

- **CRF** : Case Report Form – Formulaire médical électronique
- **CSV** : Format tabulaire (Excel-compatible)
- **JSON** : Format structuré et extensible
- **Streamlit** : Framework Python pour dashboards web
- **GitHub** : Plateforme versioning + stockage code/données
- **Mermaid** : Syntaxe text-to-diagram (flowchart, séquences, etc.)
- **Regex** : Expressions régulières pour parsing texte
- **Prophet** : Librairie Facebook pour prévisions temporelles

### B. Fichiers Existants Référencés

```
d:\université\Année II gea RH\Epifield\CRF Mpox\
├── main.py                           # Orchestrateur extraction CRF
├── dashboard_app.py                  # Dashboard Streamlit public
├── rdmStats.py                       # Générateur données synthétiques
├── analyze_extraction.py             # Normalisation + catalogue
├── analyse.py                        # Prévisions + agrégations
├── Script extraction/
│   ├── extract_word.py
│   ├── parsers.py
│   ├── aggregator.py
│   └── export.py
├── dashboard_outputs/                # Résultats finaux
└── synthetic_outputs/                # Données synthétiques
```

---

**Fin du livrable**
