================================================================================
                        SCRIPT D'ANALYSE GRAPHIQUE MPOX
                             analyse.py
================================================================================

DESCRIPTION
===========
Ce script génère un dashboard complet de visualisations et analyses pour 
les données MPox (données synthétiques ou réelles). Il crée 14 graphiques 
thématiques organisés selon les axes clés de la surveillance épidémique :
surveillance, diagnostic, infectiosité, transmission, identification des cas,
prévention et démographie.

Chaque graphique est accompagné d'intervalles de confiance (Wilson) et adapté
au contexte épidémiologique de MPox pour aider à la prise de décision 
sanitaire.

PRÉREQUIS
=========
- Python 3.6+ (recommandé 3.8+)
- Fichier d'entrée : donnees_synthetiques_flat.csv
  (généré par rdmStats.py ou exporté de données réelles)

Dépendances Python :
  • pandas
  • numpy
  • matplotlib
  • seaborn

Installation des dépendances :
  pip install pandas numpy matplotlib seaborn

UTILISATION
===========

1. Préparation
   - Assurez-vous que vous êtes dans le répertoire "Script extraction"
   - Vérifiez que synthetic_outputs/donnees_synthetiques_flat.csv existe

2. Exécution depuis la ligne de commande
   
   Option A - Depuis le répertoire Script extraction :
     python ../.venv/Scripts/Script\ Analyse/analyse.py
   
   Option B - Depuis le répertoire Script Analyse :
     python analyse.py
     (le script naviguera automatiquement vers Script extraction)
   
   Option C - Avec chemin absolu (Windows) :
     python "E:\université\Année II gea RH\Epifield\CRF Mpox\.venv\Scripts\Script Analyse\analyse.py"

3. Résultat
   Le script affiche la progression et génère les fichiers dans 
   ./dashboard_outputs/ :
   
   ✓ 14 fichiers PNG (graphiques)
   ✓ 1 fichier dashboard.html (index HTML des graphiques)

GRAPHIQUES GÉNÉRÉS
===================

Section 1 : SURVEILLANCE ET DIAGNOSTIC
--------------------------------------
1. 01_surveillance_incidence_positivite_semaine.png
   Type: Bar chart + courbe de tendance
   Vue: Volume testé par semaine + positivité par semaine
   Utilité: Surveillance temporelle de l'épidémie

2. 02_diagnostic_positivite_par_type.png
   Type: Bar chart avec IC (Wilson)
   Vue: Sensibilité comparée (lésion vs oropharynx)
   Utilité: Optimisation de la stratégie diagnostique

Section 2 : INFECTIOSITÉ ET TRANSMISSION
-----------------------------------------
3. 03a_infectiosite_ct_vs_delai_scatter.png
   Type: Scatter plot
   Vue: Relation charge virale (Ct) vs délai depuis symptômes
   Utilité: Fenêtre de détection et évolution de la viralité

4. 03b_infectiosite_ct_vs_delai_box.png
   Type: Box plot
   Vue: Distribution Ct par tranche de délai
   Utilité: Identification des patients hyper-infectieux

5. 09_infectiosite_nb_localisations_lesions.png
   Type: Bar chart
   Vue: Nombre de localisations lésionnelles
   Utilité: Étendue de la maladie et potentiel de transmission

6. 10_transmission_positivite_par_mobilite.png
   Type: Bar chart avec IC
   Vue: Positivité par groupe de mobilité/exposition
   Utilité: Identification des chaines de transmission

7. 13_transmission_nb_localisations_par_charge_virale.png
   Type: Box plot
   Vue: Nombre localisations selon charge virale (Ct catégories)
   Utilité: Corrélation infectiosité-étendue

Section 3 : IDENTIFICATION ET RISQUES
--------------------------------------
8. 04_identification_nb_symptomes_par_statut.png
   Type: Box plot
   Vue: Nombre de symptômes (PCR+ vs PCR-)
   Utilité: Sensibilité symptomatique pour dépistage

9. 05_risques_severite_par_vih.png
   Type: Stacked bar chart
   Vue: Proportion sévère selon statut VIH
   Utilité: Identification des groupes vulnérables

10. 08_qualite_indices_preanalytiques.png
    Type: Multiple bar charts
    Vue: Impact des indices pré-analytiques sur positivité
    Utilité: Contrôle qualité laboratoire

Section 4 : PRÉVENTION ET DÉMOGRAPHIE
-------------------------------------
11. 06_prevention_positivite_par_vaccin.png
    Type: Bar chart avec IC
    Vue: Positivité selon statut vaccinal
    Utilité: Évaluation efficacité vaccinale

12. 07_demographie_age_par_statut.png
    Type: Violin plot
    Vue: Distribution d'âge (PCR+ vs PCR-)
    Utilité: Profil démographique des infectés

13. 11_ciblage_positivite_par_age.png
    Type: Bar chart avec IC
    Vue: Positivité par tranche d'âge
    Utilité: Ciblage campagnes de prévention

14. 14_demographie_positivite_par_sexe.png
    Type: Bar chart avec IC
    Vue: Positivité selon sexe
    Utilité: Analyse genre-spécifique

FICHIER HTML
============

dashboard.html
  - Page HTML intégrant tous les 14 graphiques
  - Organisés par sections thématiques
  - Peut être ouvert dans n'importe quel navigateur
  - Permet une exploration interactive des résultats

Ouvrir: Double-cliquez sur dashboard.html ou ouvrez avec un navigateur

INTERPRÉTATION DES RÉSULTATS
============================

Surveillance (Graphiques 1-2)
  → Tendances épidémiologiques, efficacité diagnostique
  → Actions: Ajuster stratégie dépistage, alertes si épidémie croissante

Infectiosité (Graphiques 3-7)
  → Charge virale, durée d'infectiosité, zones à risque
  → Actions: Isolement des hyper-infectieux, ciblage contact-tracing

Identification (Graphiques 8-10)
  → Présentation clinique, vulnérabilité, QC laboratoire
  → Actions: Améliorer diagnostic, protéger groupes vulnérables

Prévention (Graphiques 11-14)
  → Efficacité vaccins, profil à risque, groupe-cibles
  → Actions: Campagnes de vaccination, sens sexo-sensibles

VARIABLES CRÉÉES EN INTERNE
===========================

Le script enrichit automatiquement les données :

- bool_cols: Conversion de colonnes texte en booléens
- *_dt: Colonnes dates converties en datetime
- delai_symptomes_vers_pcr_jours: Intervalle symptômes-test (0-20 j)
- ct_value_num: Ct numérique consolidé (lésion + oropharynx)
- charge_virale_cat: Catégories Ct (haute/moyenne/basse)
- nb_symptomes: Nombre de symptômes présents
- vih_statut: Condensé VIH (supp/non_supp/pas_ARV/négatif)
- nb_localisations_lesions: Nombre de sites lésionnels
- vaccin_type: Type(s) de vaccin reçu
- mobilite_groupe: Groupe exposition (voyage/contact/etc.)
- age_bin: Tranches d'âge OMS
- delai_bin: Tranches de délai symptômes-PCR
- severe: Booléen sévérité clinique

AMÉLIORATIONS POSSIBLES
=======================

1. Ajouter des graphiques
   - Modifier build_comparison_plan() ou ajouter directement dans main

2. Adapter les seuils
   - Les bins d'âge, délai, Ct sont définis au début du script

3. Exporter les tables de synthèse
   - Ajouter export CSV des tableaux sous-jacents

4. Ajouter des statistiques
   - Corrélations, tests statistiques (chi2, Wilcoxon, etc.)

5. Dashboard interactif
   - Migrer vers Plotly, Dash ou Streamlit

DÉPANNAGE
=========

Erreur: "FileNotFoundError: donnees_synthetiques_flat.csv not found"
  → Vérifiez que vous êtes dans le bon répertoire
  → Vérifiez que synthetic_outputs/ existe et contient les données
  → Exécutez rdmStats.py d'abord

Erreur: "ModuleNotFoundError: No module named 'matplotlib'"
  → Installez : pip install matplotlib seaborn

Les graphiques ne s'ouvrent pas
  → Vérifiez que dashboard_outputs/ existe
  → Vérifiez les permissions d'écriture

Les dates ne sont pas converties correctement
  → Adaptez le dayfirst=True/False selon votre format

Problème d'encodage (caractères spéciaux)
  → Le script utilise UTF-8
  → Assurez-vous que votre terminal supporte UTF-8

NOTES IMPORTANTES
=================

• Intervalles de confiance
  Tous les pourcentages incluent des IC 95% (Wilson)
  Permet d'évaluer la précision des estimations

• Données manquantes
  Les valeurs NaN sont traitées automatiquement
  Les graphiques s'adaptent aux données disponibles

• Sections sautées
  Si une section n'a pas de graphique : données insuffisantes
  (ex: Section 12 sautée lors du debug - tranches d'âge vides)

• Performance
  Le script est rapide même avec centaines de lignes/colonnes
  Dépend surtout du rendu matplotlib

• Reproductibilité
  Utilisez les mêmes données d'entrée pour résultats identiques
  Les graphiques sont 100% déterministes

FICHIERS CONNEXES
=================

rdmStats.py
  → Génère les données synthétiques (donnees_synthetiques_flat.csv)
  → À exécuter avant analyse.py si pas de données

extract_word.py + parsers.py + aggregator.py
  → Pipeline d'extraction depuis fichiers Word réels

analyze_extraction.py
  → Pré-analyse et classification des variables

EXEMPLE D'EXÉCUTION
===================

$ cd "Script extraction"
$ python ../.venv/Scripts/Script\ Analyse/analyse.py

[OK] Graphique cree: 01_surveillance_incidence_positivite_semaine.png
[OK] Graphique cree: 02_diagnostic_positivite_par_type.png
...
[OK] Dashboard HTML cree: dashboard_outputs\dashboard.html
Total graphiques generes: 14

→ Ouvrez dashboard_outputs/dashboard.html dans votre navigateur

CONTACT & SUPPORT
=================

Pour signaler des bugs ou proposer des améliorations :
  - Vérifiez les logs d'erreur
  - Consultez le dépannage ci-dessus
  - Adaptez les heuristiques selon vos données

================================================================================
