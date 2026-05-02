================================================================================
                        SCRIPT D'ANALYSE PRÉ-ANALYTIQUE
                            analyze_extraction.py
================================================================================

DESCRIPTION
===========
Ce script effectue une analyse structurée et préliminaire des données extraites 
des formulaires CRF MPox (Case Report Forms). Il génère un catalogue complet des 
variables avec classification automatique et crée des plans de comparaison pour 
des analyses et visualisations ultérieures.

Fonctionnalités principales :
  • Classification automatique des variables (quantitative, nominale, binaire, temporelle)
  • Détection des variables dépendantes (outcomes) vs indépendantes (prédicteurs)
  • Création de variables dérivées complexes (CT numérique, délais, comorbidités, etc.)
  • Génération dynamique de plans d'analyse adaptés aux données
  • Export de deux fichiers de référence pour analyses statistiques et visualisations

PRÉREQUIS
=========
- Python 3.6+ (recommandé 3.8+)
- Fichier d'entrée : extraction.json (généré par main.py du script d'extraction)

Dépendances Python :
  • pandas
  • numpy

Installation des dépendances :
  pip install pandas numpy

NOTE : Si vous avez utilisé le venv du projet principal, pandas et numpy 
sont déjà installés.

UTILISATION
===========

1. Préparation
   - Assurez-vous que extraction.json existe dans le même répertoire que le script
     (ou dans le répertoire parent)
   - Le fichier doit contenir les données extraites des CRF

2. Exécution depuis la ligne de commande
   
   Option A - Depuis le répertoire du script :
     python analyze_extraction.py
   
   Option B - Depuis le répertoire d'extraction (où extraction.json se trouve) :
     python ../../../.venv/Scripts/Script\ preAnalyse/analyze_extraction.py
   
   Option C - Avec chemin absolu (Windows) :
     python "E:\université\Année II gea RH\Epifield\CRF Mpox\.venv\Scripts\Script preAnalyse\analyze_extraction.py"

3. Résultat
   Le script affiche un résumé des données et génère deux fichiers dans ./outputs/ :
   
   ✓ variables_catalog.csv
     Tableau complet avec colonnes :
       - variable : nom de la variable
       - main_category : type détecté (quantitative/nominal/binary/temporal/text/unknown)
       - is_dependent : True si c'est un outcome/résultat, False sinon
       - is_temporal : True si c'est une variable temporelle
       - n_unique : nombre de valeurs uniques
       - example_values : exemple de valeurs observées
   
   ✓ comparison_plan.json
     Plans structurés pour comparaisons/graphes avec :
       - name : titre descriptif
       - type : type de graphe (bar, scatter, box, line, etc.)
       - dependent_vars : variables d'intérêt (outcomes)
       - independent_vars : variables explicatives
       - filters : filtres optionnels
       - x, y : axes ou dimensions

VARIABLES DÉRIVÉES CRÉÉES
==========================
Le script crée automatiquement :

1. Résultats PCR normalisés :
   - pcr_lesion_positif : True/False
   - pcr_oropharynx_positif : True/False
   - pcr_any_positif : True/False (si au moins une localisation positive)

2. Charge virale :
   - ct_value_num : Ct numérique consolidé
   - charge_virale_cat : Catégorisée (haute/moyenne/basse)

3. Symptomatologie :
   - nb_symptomes : Nombre total de symptômes présents
   - severe : Booléen (True si état général sévère/très malade)

4. Temporalité :
   - date_*_dt : Dates converties en datetime
   - delai_symptomes_vers_pcr_jours : Jours entre premiers symptômes et PCR

5. Comorbidités :
   - nb_comorbidites : Nombre total de comorbidités
   - vih_statut : Condensé (VIH_supp, VIH_non_supp, VIH_pas_ARV, VIH_neg_inconnu)

6. Infectiosité (pour épidémie) :
   - nb_localisations_lesions : Nombre de sites atteints
   - evolution_symptomes : Catégorie (positive/negative/stable/inconnu)

CLASSIFICATION AUTOMATIQUE
==========================
Le script utilise des heuristiques pour classer les variables :

- QUANTITATIVE : colonnes numériques, ou noms contenant
  "age", "ct", "value", "temperature", "poids", "taille", etc.

- TEMPORAL : noms contenant "date", "heure", "debut", "fin", "suivi_j"

- BINARY : résultats oui/non, 0/1, True/False

- NOMINAL : <10 valeurs uniques

- DEPENDENT : outcomes, résultats PCR, sévérité, comorbidités

INTERPRÉTATION DES RÉSULTATS
=============================

1. Nombre de variables
   Utilisé pour évaluer la complexité du dataset et la richesse des données

2. Breakdown par type
   - Quantitatives : variables pour analyses de régression, corrélations
   - Nominales/Binaires : pour stratification, analyses de contingence

3. Variables temporelles
   Importantes pour analyses de suivi longitudinal, délais

4. Variables dépendantes
   Ce sont les outcomes d'intérêt pour modélisation prédictive

5. Plans de comparaison
   Proposent automatiquement des associations pertinentes :
   - Infectiosité : CT vs délai, localisations vs charge
   - Sévérité : comorbidités vs état général
   - Mobilité : voyages/déplacements vs positivité
   - Qualité pré-analytique : indices vs résultats

AMÉLIORATIONS ET PERSONNALISATION
==================================

1. Modifier les seuils d'heuristiques
   - Éditez NUMERIC_HINTS, TEMPORAL_HINTS, OUTCOME_HINTS pour adapter la classification

2. Ajouter des variables dérivées
   - Modifiez la fonction add_derived_variables() pour ajouter vos propres dérivées

3. Étendre les plans de comparaison
   - Éditez build_comparison_plan() pour ajouter de nouveaux graphes

DÉPANNAGE
=========

Erreur : "ModuleNotFoundError: No module named 'pandas'"
  → Installez : pip install pandas numpy

Erreur : "FileNotFoundError: extraction.json not found"
  → Vérifiez que extraction.json existe dans le même répertoire
  → Assurez-vous d'avoir exécuté main.py d'abord

Les fichiers .csv ou .json ne sont pas créés
  → Vérifiez les permissions d'écriture dans le dossier ./outputs/
  → Créez manuellement le dossier ./outputs/ s'il n'existe pas

Résultat vide ou peu de plans de comparaison
  → Cela est normal si peu de variables dépendantes sont détectées
  → Modifiez OUTCOME_HINTS pour améliorer la détection

NOTES IMPORTANTES
=================

• Normalisation des noms de colonnes
  Les noms de colonnes sont normalisés : minuscules, accents supprimés, 
  espaces/caractères spéciaux → underscores

• Données manquantes
  Les valeurs NaN sont traitées correctement dans le calcul des dérivées

• Performance
  Le script est rapide même pour des centaines de variables et dizaines 
  d'enregistrements

• Flexibilité
  Les heuristiques peuvent ne pas être parfaites ; revisitez le catalogue 
  pour corriger manuellement la classification si nécessaire

FICHIERS GÉNÉRÉS
================

./outputs/variables_catalog.csv
  Référence complète pour toutes les variables et leurs propriétés

./outputs/comparison_plan.json
  Grille de comparaisons proposées pour visualisations et analyses statistiques

Ces fichiers sont destinés à :
  • Guider l'exploration de données (EDA)
  • Préparer la modélisation statistique
  • Planifier les graphes et tables à générer
  • Documenter les variables et leur rôle

EXEMPLE D'EXÉCUTION
===================

$ python analyze_extraction.py
2026-01-24 10:42:33,115 - INFO - Données chargées : 9 lignes, 104 colonnes
2026-01-24 10:42:33,159 - INFO - Catalogue créé : 104 variables classifiées
2026-01-24 10:42:33,214 - INFO - 12 variables dérivées ajoutées/mises à jour
2026-01-24 10:42:33,229 - INFO - 0 plans de comparaison générés
Résumé :
 - Enregistrements : 9
 - Variables totales : 108
 - Quantitatives : 8
 - Nominales/Binaires : 100
 - Dépendantes : 10
 - Temporelles : 5
Fichiers générés dans ./outputs : variables_catalog.csv, comparison_plan.json

================================================================================
