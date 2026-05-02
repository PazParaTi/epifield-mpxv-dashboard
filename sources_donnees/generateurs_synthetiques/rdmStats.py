
import json, random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SYNTHETIC_DATA_DIR = PROJECT_ROOT / "donnees" / "synthetiques"
SYNTHETIC_EXPORT_DIR = SYNTHETIC_DATA_DIR / "exports_script_extraction"
SYNTHETIC_DATA_DIR.mkdir(parents=True, exist_ok=True)
SYNTHETIC_EXPORT_DIR.mkdir(parents=True, exist_ok=True)

random.seed(42)
np.random.seed(42)

# Synthetic data size and period (bigger by default for seasonal experiments)
N = 900
base_date = datetime(2024,1,1)
end_date = datetime(2025,12,31)

# Regions and region-specific seasonal amplitude multipliers
regions = ['RDC','Nigeria','Kenya','Uganda','Mali','Cameroun','Autre']
region_amp = {'RDC':1.2,'Nigeria':1.1,'Kenya':1.0,'Uganda':1.0,'Mali':0.9,'Cameroun':1.05,'Autre':1.0}

# Seasonality settings: amplitude (max fractional increase), and peak month
season_amplitude = 0.4  # up to +40% positivity/incidence at peak
peak_month = 8  # August peak (approx middle of rainy season for many central African regions)

# Precompute weekly buckets between base_date and end_date
week_starts = []
cur = base_date
while cur <= end_date:
    week_starts.append(cur)
    cur += timedelta(weeks=1)
weeks = np.array(week_starts)

# Seasonal level per week (0..1) based on monthly sinusoid centered on peak_month
def season_level_for_date(d: datetime) -> float:
    # month as 1..12
    m = d.month
    # compute angle such that peak at peak_month
    angle = 2 * np.pi * ((m - peak_month) / 12.0)
    level = 0.5 * (1 + np.sin(-angle))  # maps to 0..1 with peak around peak_month
    return float(level)

# Compute week-level seasonal levels
week_levels = np.array([season_level_for_date(w) for w in weeks])

# Weight weeks by season to bias case dates towards peaks
base_week_weights = 1.0 + season_amplitude * week_levels
base_week_probs = base_week_weights / base_week_weights.sum()

sexes = ['H','F']
res_pcr_choices = ['MPXV DETECTE','MPXV NON DETECTE','INCONCLUSIF','INVALIDE']

records = []

# Sample weeks for each synthetic case according to seasonal probabilities
chosen_weeks = np.random.choice(weeks, size=N, replace=True, p=base_week_probs)

for i in range(N):
    age = int(np.clip(np.random.normal(32,12), 2, 80))
    sexe = random.choice(sexes)
    # choose week and then a random day within that week
    wk = chosen_weeks[i]
    dps = wk + timedelta(days=int(np.random.randint(0,7)))
    pcr_delay = int(np.clip(np.random.normal(4,3),0,20))
    pcr_lesion_date = dps + timedelta(days=pcr_delay)
    pcr_oro_date = pcr_lesion_date + timedelta(days=random.choice([0,0,1]))

    # Region and seasonal modulation
    region = random.choice(regions)
    reg_mult = region_amp.get(region, 1.0)
    week_level = season_level_for_date(wk)
    # probabilistic positivity baseline modulated by season and region
    prob_pos_lesion = max(0.05, (0.6 - 0.04*pcr_delay) * (1 + 0.3 * week_level * reg_mult))
    prob_pos_lesion = min(prob_pos_lesion, 0.95)
    lesion_result = np.random.choice(['MPXV DETECTE','MPXV NON DETECTE'], p=[prob_pos_lesion, 1-prob_pos_lesion])
    prob_pos_oro = max(0.02, (0.3 - 0.02*pcr_delay) * (1 + 0.25 * week_level * reg_mult))
    prob_pos_oro = min(prob_pos_oro, 0.9)
    oro_result = np.random.choice(['MPXV DETECTE','MPXV NON DETECTE'], p=[prob_pos_oro, 1-prob_pos_oro])

    # Ct cohérent: si detecté, Ct ~ N(22 + 0.8*delay, 3)
    ct_lesion = None
    if lesion_result=='MPXV DETECTE':
        ct_lesion = float(np.clip(np.random.normal(22+0.8*pcr_delay,3), 12, 40))
    ct_oro = None
    if oro_result=='MPXV DETECTE':
        ct_oro = float(np.clip(np.random.normal(26+1.0*pcr_delay,3.5), 15, 42))

    # Vaccination probabilities slightly lower in rainy season areas
    vaccin_variole = np.random.rand() < (0.12 * (1 - 0.1*week_level))
    vaccin_mva = np.random.rand() < (0.08 * (1 - 0.05*week_level))
    vaccin_varicelle = np.random.rand() < (0.25 * (1 - 0.05*week_level))

    # VIH status
    vih_charge_supprimee = np.random.rand() < 0.06
    vih_non_supprimee = (not vih_charge_supprimee) and (np.random.rand() < 0.03)
    vih_sans_arv = (not vih_charge_supprimee and not vih_non_supprimee) and (np.random.rand() < 0.02)

    # Symptômes
    symp_list = ['fievre','lesions_cutanees','toux','maux_de_tete','douleur_abdominale','nausee','vomissements']
    symptoms = {f"{s}_present": bool(np.random.rand() < 0.35) for s in symp_list}
    # Lésions cutanées plus fréquentes si PCR positive
    if lesion_result=='MPXV DETECTE' or oro_result=='MPXV DETECTE':
        symptoms['lesions_cutanees_present'] = True if np.random.rand()<0.8 else symptoms['lesions_cutanees_present']
    nb_sympt = sum(symptoms.values())

    # Sévérité approx en fonction comorbidités + nb symptômes
    comorbid_count = (1 if vih_charge_supprimee or vih_non_supprimee or vih_sans_arv else 0) + (np.random.rand()<0.07)
    severe = (nb_sympt>=4 and comorbid_count>=1) or (nb_sympt>=5)

    # Localisations (liste)
    locs_pool = ['tete','bras','jambes','tronc','bouche','paumes','plantes','genitaux','perinee','rectum']
    k = np.random.choice([1,1,2,2,3,4], p=[0.25,0.25,0.2,0.15,0.1,0.05])
    locs = ';'.join(sorted(random.sample(locs_pool, k)))

    # Mobility increases slightly during rainy season (e.g., market movements)
    antecedent_voyage = np.random.rand() < (0.18 + 0.10 * week_level)
    voyage_zone_epidemie = antecedent_voyage and (np.random.rand()<0.5)
    contact_cas_confirm_suspect = np.random.rand() < (0.22 + 0.08 * week_level)

    # Indices pré-analytiques (catégories)
    ind_levels = ['-','+','++','+++','++++']
    index_hemolytique = np.random.choice(ind_levels, p=[0.55,0.2,0.15,0.07,0.03])
    indice_lipemique = np.random.choice(ind_levels, p=[0.65,0.18,0.1,0.05,0.02])
    indice_icterique = np.random.choice(ind_levels, p=[0.7,0.15,0.1,0.04,0.01])

    rec = {
        'age': age,
        'sexe': sexe,
        'date_premiers_symptomes': dps.strftime('%d/%b/%Y'),
        'pcr_lesionnaire_date': pcr_lesion_date.strftime('%d/%b/%Y'),
        'pcr_oropharynge_date': pcr_oro_date.strftime('%d/%b/%Y'),
        'pcr_lesionnaire_resultat': lesion_result,
        'pcr_oropharynge_resultat': oro_result,
        'pcr_lesionnaire_ct_value': None if ct_lesion is None else f"{ct_lesion:.2f}",
        'pcr_oropharynge_ct_value': None if ct_oro is None else f"{ct_oro:.2f}",
        'vaccin_variole': vaccin_variole,
        'vaccin_mva': vaccin_mva,
        'vaccin_varicelle': vaccin_varicelle,
        'vih_charge_supprimee': bool(vih_charge_supprimee),
        'vih_non_supprimee': bool(vih_non_supprimee),
        'vih_sans_arv': bool(vih_sans_arv),
        'localisations': locs,
        'index_hemolytique': index_hemolytique,
        'indice_lipemique': indice_lipemique,
        'indice_icterique': indice_icterique,
        'antecedent_voyage': antecedent_voyage,
        'voyage_zone_epidemie': voyage_zone_epidemie,
        'contact_cas_confirm_suspect': contact_cas_confirm_suspect,
        **symptoms,
        'source_file': f'synthetic_case_{i:03d}.docx',
        'region': region,
        'saison_pluvieuse_level': week_level,
        'saison_pluvieuse': bool(week_level > 0.55)
    }

    records.append(rec)

# Sauver extraction synthétique
with open(SYNTHETIC_DATA_DIR / 'extraction_synthetique.json','w',encoding='utf-8') as f:
    json.dump(records,f,ensure_ascii=False,indent=2)

# Charger dans DataFrame
syn = pd.DataFrame(records)

# Appliquer un pipeline minimal (inspiré de l'analyse)
from unicodedata import normalize as uni_normalize
import re

def normalize_colname(c: str) -> str:
    c = uni_normalize('NFKD', c.lower()).encode('ascii','ignore').decode('ascii')
    c = re.sub(r'[^a-z0-9_]', '_', c)
    c = re.sub(r'_+', '_', c).strip('_')
    return c

syn.columns = [normalize_colname(c) for c in syn.columns]

# Dérivées clés
syn['pcr_lesion_positif'] = syn['pcr_lesionnaire_resultat'].str.contains('DETECTE', case=False, na=False)
syn['pcr_oropharynx_positif'] = syn['pcr_oropharynge_resultat'].str.contains('DETECTE', case=False, na=False)
syn['pcr_any_positif'] = syn['pcr_lesion_positif'] | syn['pcr_oropharynx_positif']

# Dates
for c in ['date_premiers_symptomes','pcr_lesionnaire_date','pcr_oropharynge_date']:
    syn[c+'_dt'] = pd.to_datetime(syn[c], dayfirst=True, errors='coerce')

syn['delai_symptomes_vers_pcr_jours'] = (syn['pcr_lesionnaire_date_dt'] - syn['date_premiers_symptomes_dt']).dt.days

# Ct consolidé
ct = syn['pcr_lesionnaire_ct_value'].replace('', np.nan).astype(float)
ct2 = syn['pcr_oropharynge_ct_value'].replace('', np.nan).astype(float)
syn['ct_value_num'] = ct.where(~ct.isna(), ct2)

# Charge virale cat
bins = [0,20,30,np.inf]
labels=['haute','moyenne','basse']
syn['charge_virale_cat'] = pd.cut(syn['ct_value_num'], bins=bins, labels=labels)

# Nb symptomes
symptom_cols = [c for c in syn.columns if c.endswith('_present')]
syn['nb_symptomes'] = syn[symptom_cols].sum(axis=1)

# VIH statut condensé
def vih_status(row):
    if row['vih_charge_supprimee']: return 'VIH_supp'
    if row['vih_non_supprimee']: return 'VIH_non_supp'
    if row['vih_sans_arv']: return 'VIH_pas_ARV'
    return 'VIH_neg_inconnu'

syn['vih_statut'] = syn.apply(vih_status, axis=1)

# nb localisations (compter ;) si non vide
syn['nb_localisations_lesions'] = syn['localisations'].fillna('').apply(lambda s: 0 if s=='' else s.count(';')+1)

# nb comorbidites (VIH uniquement + prob placeholder)
syn['nb_comorbidites'] = (syn[['vih_charge_supprimee','vih_non_supprimee','vih_sans_arv']].any(axis=1).astype(int) + (np.random.rand(len(syn))<0.1).astype(int))

# Evolution symptômes (simulée): à partir d’un tirage
evo_map = {0:'inconnu',1:'negative/stable',2:'positive'}
syn['evolution_symptomes'] = np.random.choice(['positive','negative/stable','inconnu'], size=len(syn), p=[0.5,0.3,0.2])

# Sauvegardes
syn.to_csv(SYNTHETIC_EXPORT_DIR / 'donnees_synthetiques_flat.csv', index=False)

# Petits agrégats utiles pour aperçu
agg = {
    'n_total': len(syn),
    'n_pcr_pos': int(syn['pcr_any_positif'].sum()),
    'positivite_%': round(100*syn['pcr_any_positif'].mean(),1),
    'ct_median_pos': float(syn.loc[syn['pcr_any_positif'],'ct_value_num'].median()),
    'delai_median_j': float(syn['delai_symptomes_vers_pcr_jours'].median()),
    'age_median': float(syn['age'].median()),
}
agg_df = pd.DataFrame([agg])
agg_df.to_csv(SYNTHETIC_EXPORT_DIR / 'aperçu_global.csv', index=False)

# Table pour graphes: positivité par semaine (de la date PCR lésionnaire)
syn['semaine'] = syn['pcr_lesionnaire_date_dt'].dt.to_period('W').astype(str)
pos_by_week = syn.groupby('semaine')['pcr_any_positif'].agg(['mean','count']).reset_index()
pos_by_week.rename(columns={'mean':'positivite','count':'n'}, inplace=True)
pos_by_week['positivite_%'] = (pos_by_week['positivite']*100).round(1)
pos_by_week.to_csv(SYNTHETIC_EXPORT_DIR / 'positivite_par_semaine.csv', index=False)

# Export JSON aussi
# Convertir datetime en string pour sérialisation JSON
syn_json = syn.copy()
for col in syn_json.columns:
    if pd.api.types.is_datetime64_any_dtype(syn_json[col]):
        syn_json[col] = syn_json[col].astype(str)
with open(SYNTHETIC_EXPORT_DIR / 'donnees_synthetiques.json','w',encoding='utf-8') as f:
    json.dump(syn_json.to_dict(orient='records'), f, ensure_ascii=False, indent=2)

print("\n[OK] Script execute avec succes!")
print(f"Fichiers generes dans {SYNTHETIC_EXPORT_DIR} et {SYNTHETIC_DATA_DIR / 'extraction_synthetique.json'}")
print(f"Aperçu: {agg}")
