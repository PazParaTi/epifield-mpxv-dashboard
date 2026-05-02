# EpiField – Architecture Technique de Plateforme de Données en Santé Publique

**Livrable : Architecture Technique Simple et Scalable**  
**Date** : Avril 2026  
**Contexte** : Prototype MPXV | Ambition : Plateforme multi-pathogènes  

---

## 1. Vue d'ensemble de l'architecture

La plateforme EpiField repose sur une **architecture en pipeline linéaire** : **Ingestion → Traitement → Enrichissement → Visualisation**. Cette approche simple garantit maintenabilité et scalabilité sans complexité superflue.

### Environnement technique
- **Langage** : Python 3.12+
- **Présentations** : Streamlit (dashboards interactifs) + Plotly (visualisations avancées)
- **Données** : CSV, JSON, parquet (extensible)
- **Orchestration** : Scripts Python exécutés en chaîne
- **Infrastructure** : Streamlit Community Cloud (gratuit, limites génériques) + GitHub (stockage + versioning)
- **Architecture de déploiement** : Serverless (pas de Docker, pas de serveurs dédiés)

---

## 2. Architecture détaillée

### 2.1 Couche d'Ingestion des Données

Deux sources de données alimentent la plateforme :

**Source 1 : Données réelles (CRF Word)**  
- Fichiers de formulaires médicaux (.docx) extraits des dossiers patients
- Pipeline d'extraction automatisée via `extract_word.py` → parseurs regex → agrégateur
- Résultat : Fichiers CSV/JSON structurés avec traçabilité
- Fréquence : À la demande (batch)

**Source 2 : Données synthétiques (fallback de développement)**  
- Script `rdmStats.py` génère 900 cas fictifs avec saisonnalité réaliste
- Intègre variabilité régionale, profils de positivité, comorbidités
- Permet tests et démos sans donner accès aux CRF réels
- Utile pour tester la scalabilité et les nouveaux indicateurs

**Sélection dynamique (switch) :**  
Au démarrage du dashboard, une variable d'environnement `DATA_MODE` détermine :
- `"synthetic"` → Charge rdmStats.py et génère les données fictives
- `"real"` → Charge les fichiers d'extraction réelle depuis le dépôt

---

### 2.2 Couche de Traitement et Enrichissement

**Normalisation et catalogage (`analyze_extraction.py`)**
- Classification automatique des 100+ variables en 4 catégories :
  - Quantitatives (âge, charge virale, Ct)
  - Nominales (région, type de lesion, pathogène)
  - Binaires (vaccin, sévérité, résultat PCR)
  - Temporelles (date symptômes, semaine de prélèvement)
- Génération de variables dérivées (positivité par strate, délais, comorbidités)
- Export d'un catalogue exhaustif pour documentation

**Analyse et prévision (`analyse.py`)**
- Nettoyage de données (imputations, détection aberrantes)
- Calcul d'indicateurs agrégés : incidence, positivité, sévérité
- Prévisions temporelles (Prophet, Exponential Smoothing)
- Génération de graphiques statistiques haute résolution
- Export agrégé par niveaux : local (cas), national (région), international

**Résultats intermédiaires :**
- `data_local.csv` : Niveau cas (détail complet)
- `data_national.csv` : Agrégations régionales/nationales
- `data_international.csv` : Comparaisons inter-pays
- `national_forecast.csv` : Prévisions 12 semaines

---

### 2.3 Couche de Présentation

**Dashboard interactif (Streamlit + Plotly)**
- Interface web responsive, déployée publiquement
- Filtres en temps quasi-réel (région, semaine, pathogène)
- 14+ visualisations interactives
- Indicateurs clés animés (KPI avec codes couleur et emojis)
- Performance : Chargement < 2 secondes (optimisation cache Streamlit)

**Visualisations statiques (fallback)**
- Dashboards HTML auto-générés (local, national, international)
- PNG haute résolution pour rapports

---

## 3. Infrastructure et déploiement

### 3.1 Architecture cloud simplifiée

```
┌─────────────────────────────────────────────────┐
│      GitHub Repository (Source de vérité)      │
│ - Code Python + Scripts extraction              │
│ - Données synthétiques + données réelles        │
│ - requirements.txt + runtime.txt                │
│ - Secrets: Auth tokens, API keys (.env.local)   │
└─────────────────────────────────────────────────┘
                    ↓ Git Pull
┌─────────────────────────────────────────────────┐
│  Streamlit Community Cloud (Déploiement)        │
│ - Serverless Python runtime (3.12)              │
│ - Auto-redéploiement à chaque push GitHub       │
│ - Cache intégré (stockage session)              │
│ - Domaine public gratuit                        │
│ - Limites : 1 Go RAM, rafraîchissement ~30s     │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│    Utilisateurs Finaux                          │
│ - Epidémiologistes : Monitoring épidémie        │
│ - Gestionnaires : Prévisions et alertes         │
│ - Scientifiques : Données exportables           │
└─────────────────────────────────────────────────┘
```

### 3.2 Pipeline d'exécution

1. **Ingestion** : Un administrateur pousse des CRF Word dans le dépôt GitHub
2. **Extraction** : Script `main.py` parse les Word → CSV/JSON (exécution locale ou GitHub Actions)
3. **Traitement** : Scripts `analyze_extraction.py` + `analyse.py` enrichissent les données
4. **Déploiement** : Commit → GitHub → Streamlit détecte le push → Redéploie le dashboard automatiquement
5. **Consultation** : Utilisateurs accèdent au lien public, interagissent en direct

**Temps d'exécution** : 2-3 minutes pour une mise à jour complète (extraction + traitement)

---

## 4. Avantages de cette architecture

| Critère | Bénéfice |
|---------|----------|
| **Simplicité** | Pas d'orchestrateur externe (Airflow, Kubernetes), pas de Docker → déploiement en quelques clics |
| **Coût** | 100% gratuit (GitHub + Streamlit Community Cloud) |
| **Scalabilité multi-pathogènes** | Parseurs généralisables à d'autres pathogènes (grippe, COVID, etc.) |
| **Temps réel** | Rafraîchissement des données < 5 minutes après mise à jour GitHub |
| **Traçabilité** | Historique complet des données et transformations dans Git |
| **Sécurité** | Données synthétiques par défaut ; accès réel contrôlé via variables d'env |
| **Extensibilité** | Pipeline modulaire : ajouter un nouveau parseur = créer une fonction Python |

---

## 5. Switch synthétique ↔ réel

Mécanisme clé pour développement et déploiement sécurisé :

```python
# dashboard_app.py
MODE = os.getenv("DATA_MODE", "synthetic")

if MODE == "synthetic":
    data = rdmStats.generate_synthetic_data()
else:
    data = pd.read_csv("extraction_real.json")
```

**En pratique :**
- **Environnement local** : `DATA_MODE=synthetic` → tests sans données sensibles
- **Environnement prod (Streamlit Cloud)** : `DATA_MODE=real` → données CRF après nettoyage RGPD
- **Branche git** : Deux fichiers `extraction_real.json` versionnés de manière anonyme

---

## 6. Roadmap d'évolution

**Court terme (M1-2)** :
- Intégration d'une deuxième pathogène (grippe)
- Historique versioning des données (audit trail)

**Moyen terme (M3-6)** :
- API GraphQL pour requêtes avancées (au lieu de télécharger CSV)
- Alertes automatisées (email/SMS si seuils épidémiologiques dépassés)
- Base de données PostgreSQL (remplace CSV) pour concurrence et historique temps-réel

**Long terme (M6+)** :
- Infrastructure privée avec Docker Compose pour sensibilité données accrue
- Authentification OIDC (SSO) et contrôle d'accès granulaire
- ML-Ops : Retraining automatique des prévisions

---

## 7. Conclusion

EpiField propose une **architecture pragmatique et économe** adaptée aux réalités des ressources de santé publique. Le design modulaire en pipeline linéaire offre clarté et flexibilité. Le switch synthétique/réel garantit sécurité données pendant la phase prototype. Aucune complexité technique ne ralentit l'itération : la première brique technologique complète peut être en production en **une semaine**.

---

**Version** : 1.0 | **Autorité** : Architecture technique EpiField | **Prochaine revue** : Juillet 2026
