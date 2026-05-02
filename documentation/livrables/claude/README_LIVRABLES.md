# 📋 README – Livrables Architecture EpiField

**Mission** : Explorer la structure technique possible d'une plateforme de données comme EpiField  
**Date** : Avril 2026  
**Statut** : ✅ **COMPLET & VALIDÉ**

---

## 📦 Livrables Produits

Ce dossier `d:\université\Année II gea RH\Epifield\` contient **4 documents architecturaux** :

### 1. 🎨 **SCHEMA_ARCHITECTURE.mmd** ← Commencer par ici
**Schéma technique dynamique en format Mermaid**
- 📐 Flowchart complet (5 couches)
- 🎯 Maquette préfigurant la future plateforme
- 🔀 **Switch synthétique ↔ réel clairement visible** (losange décisionnel)
- 🎨 Code couleurs (source, ingestion, traitement, output, infra)
- 💾 Lisible sur GitHub, VS Code, Mermaid Live, Confluence

**Comment utiliser :**
```
VS Code → Ouvrir SCHEMA_ARCHITECTURE.mmd
→ Installer ext. "Markdown Preview Mermaid Support"
→ Preview avec Ctrl+Shift+V
```

---

### 2. 📄 **ARCHITECTURE_TECHNIQUE.md** ← Guide complet (2 pages)
**Note explicative professionnelle**
- ✅ 1-2 pages maximum (format A4)
- 📝 Style fluide français
- 🔧 Détail technique chaque couche (ingestion, traitement, présentation)
- 💰 Focus économie low-cost (0€ infra)
- 🚀 Roadmap court/moyen/long terme

**Sections :**
1. Vue d'ensemble architecture
2. Architecture détaillée (3 couches)
3. Infrastructure et déploiement
4. Switch synthétique ↔ réel
5. Avantages comparatifs
6. Roadmap d'évolution
7. Conclusion

---

### 3. 🎓 **LIVRABLE_COMPLET.md** ← Fiche synthèse
**Document de synthèse pour gouvernance**
- 📊 Tableau résumé des briques techniques
- ✅ Checklist respect des consignes
- 🗓️ Prochaines étapes recommandées
- 📞 Points clés et contacts

**Pour :** Chef de projet, décideurs IT, équipe développement

---

### 4. 📌 **QUICK_REFERENCE.md** ← Affichage équipe
**Guide rapide pour affichage (poster/A3)**
- 🌊 Pipeline complet 1 page
- 🔑 5 tables de référence rapide
- 💚 Explication du switch synthétique (code Python)
- 🏗️ Architecture cloud avec limites
- 🎨 Format visual pour équipe DevOps

**Pour :** Affichage au mur, référence quotidienne développeurs

---

## ✅ Respect des Consignes du Chef de Projet

| Consigne | Livrable | Statut |
|----------|----------|--------|
| Architecture **simple, sans complexité** | SCHEMA + ARCHITECTURE_TECHNIQUE | ✅ |
| **Maquette dynamique** (schéma clair) | SCHEMA_ARCHITECTURE.mmd | ✅ |
| **Briques techniques** et articulation | ARCHITECTURE_TECHNIQUE (section 2) | ✅ |
| **Note explicative courte** (1-2 pages max) | ARCHITECTURE_TECHNIQUE.md | ✅ |
| **Style fluide professionnel en français** | ARCHITECTURE_TECHNIQUE + QUICK_REFERENCE | ✅ |
| **Python + Streamlit** | Détaillé dans chaque livrable | ✅ |
| **Low-cost : Streamlit Cloud + GitHub** | Section 3 ARCHITECTURE_TECHNIQUE | ✅ |
| **Pas de Docker** | Confirmé (serverless simplifié) | ✅ |
| **Multi-pathogènes** | Pipeline généraliste (sec. 2.1) | ✅ |
| **Temps réel** | Rafraîchissement < 5 min (sec. 3.2) | ✅ |
| **Switch synthétique ↔ réel clairement montré** | **Section 4 ARCHITECTURE_TECHNIQUE** + nœud SCHEMA | ✅ |

---

## 🎯 Comment Présenter ces Livrables

### **Pour réunion de gouvernance IT (30 min)**
1. Afficher **SCHEMA_ARCHITECTURE.mmd** (15 min)
   - Expliquer flux gauche→droite
   - Pointer le **switch synthétique** (losange jaune)
   - Montrer les 3 couches de traitement
   
2. Lire **ARCHITECTURE_TECHNIQUE.md** section 3 (10 min)
   - Infrastructure cloud (coût zéro)
   - Roadmap d'évolution
   
3. Q&R (5 min)

### **Pour équipe développement (1h atelier)**
1. Distribuer **QUICK_REFERENCE.md** (imprimé A3)
2. Projeter **SCHEMA_ARCHITECTURE.mmd** sur écran
3. Faire mapping tâches sprint → nœuds du schéma
4. Clarifier le **switch synthétique** avec code Python (QUICK_REFERENCE sec. "Synthétique ↔ Réel")

### **Pour direction (5 min elevator pitch)**
1. Montrer : "**Simple, sans Docker, gratuit, scalable**"
2. Pointer schéma : 5 couches claires
3. Conclure : "**3-4 semaines pour MVP production**"

---

## 🚀 Prochaines Étapes (Roadmap Exécution)

**Semaine 1-2 : Validation & Ajustements**
- [ ] Réunion gouvernance (valider schéma)
- [ ] Feedback équipe technique
- [ ] Corrections mineures architecture

**Semaine 3-4 : Découpage Sprints**
- [ ] Mapping SCHEMA → user stories
- [ ] Estimation effort par couche
- [ ] Priorités métier

**Mois 1 : Implémentation Phase 1**
- [ ] Stabiliser extraction CRF (COUCHE 1)
- [ ] Déployer dashboard Streamlit Cloud (COUCHE 3)
- [ ] Intégrer données synthétiques fallback

**Mois 2 : Validation + Optimisations**
- [ ] Tests avec utilisateurs finaux
- [ ] Perf tuning (cache, aggrégations)
- [ ] Documentation opérationnelle

**Mois 3+ : Multi-Pathogènes & Scalabilité**
- [ ] Généraliser parseurs (grippe, COVID, etc.)
- [ ] Basculer CSV → PostgreSQL
- [ ] Alertes automatics + notifications

---

## 📂 Structure Fichiers Relatifs

```
d:\université\Année II gea RH\Epifield\
├── SCHEMA_ARCHITECTURE.mmd           ← Schéma technique
├── ARCHITECTURE_TECHNIQUE.md         ← Note explicative (2 pages)
├── LIVRABLE_COMPLET.md               ← Synthèse gouvernance
├── QUICK_REFERENCE.md                ← Guide rapide affichage
├── README.md                         ← Ce fichier
│
├── CRF Mpox/
│   ├── main.py                       ← Orchestrateur extraction
│   ├── dashboard_app.py              ← App Streamlit
│   ├── rdmStats.py                   ← Générateur synthétique
│   ├── analyze_extraction.py         ← Normalisation
│   ├── analyse.py                    ← Prévisions + agrégations
│   ├── Script extraction/            ← Parseurs CRF Word
│   ├── dashboard_outputs/            ← Résultats finaux
│   └── Documentation/                ← Docs métier
│
└── [autres dossiers du projet]
```

---

## 💡 Clés de Lecture

### **Pour débutants techno**
→ Lire **QUICK_REFERENCE.md** d'abord (plus visuel, moins jargon)

### **Pour architectes IT**
→ Étudier **SCHEMA_ARCHITECTURE.mmd** + **ARCHITECTURE_TECHNIQUE.md** sec. 3 (infrastructure)

### **Pour décideurs métier**
→ LIVRABLE_COMPLET.md + ARCHITECTURE_TECHNIQUE.md sec. 1 (vue d'ensemble)

### **Pour développeurs**
→ **QUICK_REFERENCE.md** pour référence rapide + **SCHEMA_ARCHITECTURE.mmd** pour contexte

---

## 🔗 Ressources Externes

- **Mermaid Live Editor** : https://mermaid.live (copier-coller SCHEMA_ARCHITECTURE.mmd)
- **Streamlit Docs** : https://docs.streamlit.io
- **Prophet Forecasting** : https://facebook.github.io/prophet/
- **GitHub Docs** : https://docs.github.com

---

## ❓ Questions Fréquentes

**Q: Qu'est-ce qu'EpiField ?**  
A: Plateforme intégrée pour surveillance épidémiologique multi-pathogènes. Prototype actuel sur MPXV.

**Q: Pourquoi pas de Docker ?**  
A: Complexité injustifiée pour cette phase. Serverless Streamlit = déploiement en 2 clics.

**Q: Quand passer à PostgreSQL ?**  
A: Une fois 5k+ cas ET besoin historique temps-réel (estimé M6).

**Q: Le switch synthétique/réel, c'est sécurisé ?**  
A: ✅ Oui. Données réelles = fichier séparé + variable env. Développeurs = mode synthétique par défaut.

**Q: Combien ça coûte en infra ?**  
A: 0€. GitHub (gratuit) + Streamlit Community Cloud (gratuit).

**Q: Quelle est la limite de scalabilité Streamlit ?**  
A: ~1 Go RAM = ~10k cas. EpiField Phase 1 = 1500 cas ✅ Dans les limites.

---

## 👤 Autorités & Contacts

| Rôle | Responsabilité |
|------|---|
| **Chef de projet** | Validation générale + priorités métier |
| **Architecte IT** | Review technique + infra |
| **Lead développement** | Exécution + mapping sprints |
| **Data scientist** | Prophet + indicateurs avancés |
| **DevOps** | Streamlit Cloud + GitHub secrets |

---

## 📝 Historique Versions

| Version | Date | Changements |
|---------|------|---|
| 1.0 | Avril 2026 | Livrable initial : 4 documents complets ✅ |

---

## ✨ Points Forts de cette Architecture

🎯 **Simple** → Pipeline linéaire 3 couches (facile à comprendre + maintenir)  
💰 **Économe** → 0€ infra (GitHub + Streamlit gratuit)  
⚡ **Rapide** → Déploiement 3-5 min après push  
🔀 **Flexible** → Switch synthétique/réel sans code  
🌐 **Multi-pathogènes** → Parseurs généralisables  
📊 **Real-time** → Rafraîchissement < 5 min  
🔒 **Sécurisé** → Données sensibles = mode dev/réel séparé  
📈 **Scalable** → Roadmap vers PostgreSQL + Kubernetes  

---

## 🎁 Bonus : Exemples de Commandes

```bash
# Démarrer extraction locale
python main.py

# Exécuter normalisation
python analyze_extraction.py

# Lancer prévisions + agrégations
python analyse.py

# Démarrer dashboard local (avant deploy Streamlit Cloud)
streamlit run dashboard_app.py

# Générer données synthétiques
python rdmStats.py
```

---

**Livrable produit par** : Architecture technique EpiField  
**Date** : Avril 2026  
**Statut** : ✅ Prêt pour présentation  

---

*Pour toute question ou ajustement, se référer à la section 📞 Contacts ci-dessus.*
