# -*- coding: utf-8 -*-
"""
analyze_extraction.py
Base d'analyse des données extraites des CRF MPXV.

Améliorations apportées :
- Amélioration de la robustesse : Normalisation des noms de colonnes (minuscules, suppression accents, espaces → _).
- Classification des variables : Ajout de détection automatique des types (numérique, catégoriel avec n_unique, booléen), meilleure heuristique pour temporel/dépendant.
- Variables dérivées : Ajout de plus de dérivées (nb_localisations_lesions, nb_comorbidites, evolution_symptomes, charge_virale_cat, etc.), gestion des variations de noms de colonnes.
- Plan de comparaisons : Rendu plus dynamique (généré à partir du catalogue), ajout de filtres et types de graphs adaptés, plus de groupes pour prédiction épidémie (mobilité, infectiosité, sévérité).
- Ajout de nettoyage de base : Drop colonnes vides, gestion NaN pour dérivées.
- Logging : Ajout de logs pour débogage.
- Efficacité : Utilisation vectorisée Pandas où possible.

Exécution :
    python analyze_extraction.py

Sorties (dans ./outputs) :
    - variables_catalog.csv  (variable, main_category, is_dependent, is_temporal, n_unique, example_values)
    - comparison_plan.json   (groupes nommés pour les comparaisons/graphes, plus dynamiques)
"""

import json
import re
from pathlib import Path
from typing import List, Dict
import logging
from unicodedata import normalize as uni_normalize

import pandas as pd
import numpy as np

# Configuration logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REAL_DATA_PATH = PROJECT_ROOT / "donnees" / "reelles" / "extraction.json"
CATALOG_DIR = PROJECT_ROOT / "traitement" / "catalogue_variables"


# ============ 1) CHARGEMENT ET NETTOYAGE INITIAL ============

def normalize_colname(c: str) -> str:
    """Normalise nom de colonne : minuscules, sans accents, espaces → _, suppression caractères spéciaux."""
    c = uni_normalize("NFKD", c.lower()).encode("ascii", "ignore").decode("ascii")
    c = re.sub(r"[^a-z0-9_]", "_", c)
    c = re.sub(r"_+", "_", c).strip("_")
    return c

def load_data(json_path: str = "extraction.json") -> pd.DataFrame:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    
    # Normaliser noms de colonnes
    df.columns = [normalize_colname(c) for c in df.columns]
    
    # Drop colonnes vides
    df = df.dropna(axis=1, how="all")
    
    logger.info(f"Données chargées : {df.shape[0]} lignes, {df.shape[1]} colonnes")
    return df


# ============ 2) OUTILS D'INFÉRENCE DE TYPE ============

NUMERIC_HINTS = [
    "age", "ct", "value", "valeur", "temperature", "tension", "frequence",
    "poids", "taille", "mm", "volume", "nombre", "count", "vitesse", "temps",
    "time", "heures", "hour", "min", "ml", "ul", "index", "indice", "delai", "jours"
]
TEMPORAL_HINTS = ["date", "heure", "timepoint", "time_point", "debut", "fin", "suivi_j"]
OUTCOME_HINTS = [
    "result", "resultat", "ct", "statut", "symptome", "symptomes", "etat_general",
    "run_pass", "hemcheck", "positif", "severe", "nb_symptomes"
]

def classify_variables(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for col in df.columns:
        series = df[col].dropna()
        n_unique = series.nunique()
        example_vals = series.unique()[:5].tolist() if len(series) > 0 else []
        
        cname = col.lower()
        is_temporal = any(h in cname for h in TEMPORAL_HINTS)
        numeric_hint = any(h in cname for h in NUMERIC_HINTS)
        
        if series.empty:
            main_type = "unknown"
        elif pd.api.types.is_bool_dtype(series) or set(series.unique()).issubset({0, 1, True, False, "oui", "non", "o", "n"}):
            main_type = "binary"
        elif pd.api.types.is_numeric_dtype(series) or (numeric_hint and is_numeric_series(series)):
            main_type = "quantitative"
        elif is_temporal or pd.api.types.is_datetime64_any_dtype(series):
            main_type = "temporal"
        elif n_unique <= 10:  # Arbitraire, mais pour catégoriel
            main_type = "nominal"
        else:
            main_type = "text/other"
        
        is_dependent = any(h in cname for h in OUTCOME_HINTS) or "positif" in cname or "severe" in cname
        
        rows.append({
            "variable": col,
            "main_category": main_type,
            "is_dependent": is_dependent,
            "is_temporal": is_temporal,
            "n_unique": n_unique,
            "example_values": str(example_vals)
        })
    catalog = pd.DataFrame(rows)
    logger.info(f"Catalogue créé : {len(catalog)} variables classifiées")
    return catalog

def is_numeric_series(series: pd.Series) -> bool:
    try:
        pd.to_numeric(series.astype(str).str.replace(",", ".", regex=False), errors="raise")
        return True
    except Exception:
        return False


# ============ 2.5) UTILITAIRES ============

def normalize_result(x):
    """Normalise les résultats PCR."""
    if pd.isna(x):
        return None
    s = str(x).strip().lower()
    if "detect" in s or "posit" in s:
        return "positif"
    if "non" in s or "negat" in s:
        return "negatif"
    if "inconclu" in s:
        return "inconclusif"
    if "inval" in s:
        return "invalide"
    return None

def try_to_float(x):
    """Convertit une valeur en float."""
    if pd.isna(x):
        return np.nan
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x).strip().replace(",", ".")
    if s == "":
        return np.nan
    try:
        return float(s)
    except ValueError:
        return np.nan


# ============ 3) VARIABLES DÉRIVÉES ============

def add_derived_variables(df: pd.DataFrame, catalog: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    
    # PCR résultat → bool (gestion variations noms)
    lesion_cols = [c for c in df.columns if "pcr_lesion" in c and "resultat" in c]
    oro_cols = [c for c in df.columns if "pcr_oro" in c and "resultat" in c]
    
    res_lesion = df[lesion_cols[0]] if lesion_cols else None
    res_oro = df[oro_cols[0]] if oro_cols else None
    
    if res_lesion is not None:
        df["pcr_lesion_positif"] = res_lesion.map(normalize_result).eq("positif")
    if res_oro is not None:
        df["pcr_oropharynx_positif"] = res_oro.map(normalize_result).eq("positif")
    
    # CT → numérique consolidé
    ct_cols = [c for c in df.columns if "ct_value" in c]
    ct_num = pd.Series(np.nan, index=df.index)
    for c in ct_cols:
        n = df[c].apply(try_to_float)
        ct_num = ct_num.fillna(n)
    if not ct_num.isna().all():
        df["ct_value_num"] = ct_num
        # Ajout catégorie charge virale
        df["charge_virale_cat"] = pd.cut(df["ct_value_num"], bins=[0, 20, 30, np.inf], labels=["haute", "moyenne", "basse"])
    
    # Nombre de symptômes présents
    symptom_cols = [c for c in df.columns if c.endswith("_present") and "oui" not in c]  # Éviter doublons
    if symptom_cols:
        df["nb_symptomes"] = df[symptom_cols].sum(axis=1, skipna=True)
    
    # Sévérité (état général)
    if "etat_general" in df.columns:
        df["severe"] = df["etat_general"].str.contains("tres_malade|modere", case=False, na=False)  # Élargi à modéré
    
    # PCR any positif
    if "pcr_lesion_positif" in df.columns or "pcr_oropharynx_positif" in df.columns:
        df["pcr_any_positif"] = df.get("pcr_lesion_positif", False) | df.get("pcr_oropharynx_positif", False)
    
    # Dates → délais (généralisé)
    # Dates → délais (généralisé)
    date_cols = []
    for c in df.columns:
        if "date" in c:
            matches = catalog[catalog["variable"] == c]
            if not matches.empty and matches["is_temporal"].iloc[0]:
                date_cols.append(c)
    for dc in date_cols:
        df[dc + "_dt"] = pd.to_datetime(df[dc], dayfirst=True, errors="coerce")
    
    # Délai symptômes → PCR
    sympt_dt = df.get("date_premiers_symptomes_dt")
    pcr_dt_cols = [c for c in df.columns if "pcr_" in c and "_date_dt" in c]
    if sympt_dt is not None and pcr_dt_cols:
        pcr_dt = df[pcr_dt_cols[0]]  # Prendre le premier disponible
        df["delai_symptomes_vers_pcr_jours"] = (pcr_dt - sympt_dt).dt.days.clip(lower=0)
    
    # Statut VIH condensé
    vih_cols = [c for c in df.columns if "vih_" in c]
    if any("vih" in c for c in df.columns):
        def vih_status(row):
            if any(row.get(c, False) for c in vih_cols if "supprimee" in c):
                return "VIH_supp"
            if any(row.get(c, False) for c in vih_cols if "non_supprimee" in c):
                return "VIH_non_supp"
            if any(row.get(c, False) for c in vih_cols if "sans_arv" in c):
                return "VIH_pas_ARV"
            return "VIH_neg_inconnu"
        df["vih_statut"] = df.apply(vih_status, axis=1)
    
    # Ajouts pour prédiction épidémie
    # Nb localisations lésions
    if "localisations" in df.columns:
        df["nb_localisations_lesions"] = df["localisations"].str.count(";") + 1  # +1 si non vide
    
    # Nb comorbidités - convertir booléens/binaires et compter
    comorb_cols = [c for c in df.columns if "comorbid" in c or "vih" in c or "malnutrition" in c or "ist" in c or "tumeur" in c]
    if comorb_cols:
        comorb_numeric = df[comorb_cols].copy()
        # Convertir les colonnes en numériques (booléen → 1/0)
        for col in comorb_numeric.columns:
            comorb_numeric[col] = comorb_numeric[col].apply(lambda x: 1 if pd.notna(x) and (x == True or x == "Oui" or x == "oui" or x == 1) else 0)
        df["nb_comorbidites"] = comorb_numeric.sum(axis=1, skipna=True)
    
    # Évolution symptômes (basé sur suivis)
    suivi_cols = [c for c in df.columns if "suivi_j" in c and "symptomes" in c]
    if suivi_cols:
        def evolution_sympt(row):
            states = [row[c] for c in suivi_cols if pd.notna(row[c])]
            if not states:
                return "inconnu"
            if states[-1] in ["guerison", "amelioration"]:
                return "positive"
            return "negative/stable"
        df["evolution_symptomes"] = df.apply(evolution_sympt, axis=1)
    
    # Mise à jour catalogue pour dérivées
    derived_map = {
        "pcr_lesion_positif": ("binary", True, False),
        "pcr_oropharynx_positif": ("binary", True, False),
        "ct_value_num": ("quantitative", True, False),
        "charge_virale_cat": ("nominal", True, False),
        "nb_symptomes": ("quantitative", True, False),
        "severe": ("binary", True, False),
        "pcr_any_positif": ("binary", True, False),
        "delai_symptomes_vers_pcr_jours": ("quantitative", False, False),
        "vih_statut": ("nominal", False, False),
        "nb_localisations_lesions": ("quantitative", True, False),
        "nb_comorbidites": ("quantitative", False, False),
        "evolution_symptomes": ("nominal", True, False),
    }
    cat_rows = []
    for var, (typ, dep, temp) in derived_map.items():
        if var in df.columns:
            n_unique = df[var].nunique()
            examples = df[var].unique()[:5].tolist()
            cat_rows.append({
                "variable": var,
                "main_category": typ,
                "is_dependent": dep,
                "is_temporal": temp,
                "n_unique": n_unique,
                "example_values": str(examples)
            })
    if cat_rows:
        new_cat = pd.DataFrame(cat_rows)
        catalog = pd.concat([catalog, new_cat], ignore_index=True)
        catalog = catalog.drop_duplicates(subset=["variable"], keep="last")
    
    logger.info(f"{len(derived_map)} variables dérivées ajoutées/mises à jour")
    return df, catalog


# ============ 4) PLAN DE COMPARAISONS (GRAPHES) DYNAMIQUE ============

def build_comparison_plan(catalog: pd.DataFrame) -> List[Dict]:
    """
    Génère dynamiquement des plans basés sur catalogue : lie outcomes (dépendantes) à covariables (indépendantes).
    Priorité aux variables critiques pour épidémie : démographie, mobilité, infectiosité, sévérité.
    """
    deps = catalog[catalog["is_dependent"]]["variable"].tolist()
    indeps = catalog[~catalog["is_dependent"] & (catalog["main_category"].isin(["quantitative", "nominal", "binary"]))]["variable"].tolist()
    temps = catalog[catalog["is_temporal"]]["variable"].tolist()
    
    plans = []
    
    # Plans statiques améliorés + dynamiques
    if "pcr_any_positif" in deps:
        plans.append({
            "name": "Positivité PCR par type d’échantillon",
            "type": "bar",
            "x": "type_echantillon",
            "y": "proportion_positive",
            "groups": ["pcr_lesion_positif", "pcr_oropharynx_positif"],
            "dependent_vars": ["pcr_any_positif"],
            "independent_vars": []
        })
    
    if "ct_value_num" in deps and "delai_symptomes_vers_pcr_jours" in indeps:
        plans.append({
            "name": "CT vs délai (symptômes → PCR)",
            "type": "scatter",
            "x": "delai_symptomes_vers_pcr_jours",
            "y": "ct_value_num",
            "filters": ["pcr_any_positif == True"],
            "dependent_vars": ["ct_value_num"],
            "independent_vars": ["delai_symptomes_vers_pcr_jours"]
        })
    
    if "nb_symptomes" in deps and "pcr_any_positif" in indeps:
        plans.append({
            "name": "Nombre de symptômes par statut PCR",
            "type": "box",
            "x": "pcr_any_positif",
            "y": "nb_symptomes",
            "dependent_vars": ["nb_symptomes"],
            "independent_vars": ["pcr_any_positif"]
        })
    
    if "severe" in deps and "vih_statut" in indeps:
        plans.append({
            "name": "Sévérité clinique par comorbidité VIH",
            "type": "stacked_bar",
            "x": "vih_statut",
            "y": "proportion_severe",
            "dependent_vars": ["severe"],
            "independent_vars": ["vih_statut"]
        })
    
    vacc_cols = [c for c in indeps if "vaccin" in c]
    if vacc_cols and "pcr_any_positif" in deps:
        plans.append({
            "name": "Positivité PCR selon statut vaccinal",
            "type": "grouped_bar",
            "x": "vaccin_type",
            "y": "proportion_positive",
            "dependent_vars": ["pcr_any_positif"],
            "independent_vars": vacc_cols
        })
    
    if "age" in indeps and "pcr_any_positif" in deps:
        plans.append({
            "name": "Distribution de l’âge selon statut PCR",
            "type": "violin",
            "x": "pcr_any_positif",
            "y": "age",
            "dependent_vars": ["age"],  # Age peut être vu comme dépendant ici? Inversé pour distro
            "independent_vars": ["pcr_any_positif"]
        })
    
    # Ajouts pour épidémie : Mobilité
    mob_cols = [c for c in indeps if "voyage" in c or "deplacement" in c or "zone" in c]
    if mob_cols and "pcr_any_positif" in deps:
        plans.append({
            "name": "Positivité PCR par mobilité (voyages/zones risque)",
            "type": "grouped_bar",
            "x": "mobilite_groupe",
            "y": "proportion_positive",
            "dependent_vars": ["pcr_any_positif"],
            "independent_vars": mob_cols
        })
    
    # Infectiosité : lésions, Ct, localisations
    if "nb_localisations_lesions" in deps and "charge_virale_cat" in deps:
        plans.append({
            "name": "Infectiosité : Nb localisations vs charge virale",
            "type": "box",
            "x": "charge_virale_cat",
            "y": "nb_localisations_lesions",
            "dependent_vars": ["nb_localisations_lesions"],
            "independent_vars": ["charge_virale_cat"]
        })
    
    # Sévérité par comorbidités
    if "nb_comorbidites" in indeps and "severe" in deps:
        plans.append({
            "name": "Sévérité par nombre de comorbidités",
            "type": "bar",
            "x": "nb_comorbidites",
            "y": "proportion_severe",
            "dependent_vars": ["severe"],
            "independent_vars": ["nb_comorbidites"]
        })
    
    # Évolution temporelle si suivis
    if "evolution_symptomes" in deps and temps:
        plans.append({
            "name": "Évolution symptômes au fil du suivi",
            "type": "line",
            "x": "jour_suivi",
            "y": "proportion_positive_evolution",
            "dependent_vars": ["evolution_symptomes"],
            "independent_vars": temps
        })
    
    # QC labo si indices
    qc_cols = [c for c in indeps if "indice" in c or "hemolytique" in c or "lipemique" in c]
    if qc_cols and "pcr_any_positif" in deps:
        plans.append({
            "name": "Qualité pré-analytique vs résultat PCR",
            "type": "grouped_bar",
            "x": "indice_type",
            "y": "proportion_positive",
            "dependent_vars": ["pcr_any_positif"],
            "independent_vars": qc_cols
        })
    
    logger.info(f"{len(plans)} plans de comparaison générés")
    return plans


# ============ 5) MAIN ============

def main():
    df = load_data(REAL_DATA_PATH)
    
    # 1) Catalogue initial
    catalog = classify_variables(df)
    
    # 2) Variables dérivées + mise à jour du catalogue
    df, catalog = add_derived_variables(df, catalog)
    
    # 3) Plan de comparaisons
    plan = build_comparison_plan(catalog)
    
    # 4) Sauvegardes
    outdir = CATALOG_DIR
    outdir.mkdir(parents=True, exist_ok=True)
    catalog.sort_values("variable").to_csv(outdir / "variables_catalog.csv", index=False)
    with open(outdir / "comparison_plan.json", "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)
    
    # 5) Récap console
    nb_quant = (catalog["main_category"] == "quantitative").sum()
    nb_nom = (catalog["main_category"].isin(["nominal", "binary"])).sum()
    nb_dep = catalog["is_dependent"].sum()
    nb_temp = catalog["is_temporal"].sum()
    
    print("Résumé :")
    print(" - Enregistrements :", len(df))
    print(" - Variables totales :", df.shape[1])
    print(" - Quantitatives :", int(nb_quant))
    print(" - Nominales/Binaires :", int(nb_nom))
    print(" - Dépendantes :", int(nb_dep))
    print(" - Temporelles :", int(nb_temp))
    print(f"Fichiers generes dans {outdir} : variables_catalog.csv, comparison_plan.json")

if __name__ == "__main__":
    main()
