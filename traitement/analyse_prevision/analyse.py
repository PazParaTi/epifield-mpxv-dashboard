import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import os
import warnings
warnings.filterwarnings('ignore')
# Optional forecasting library (prophet). If missing, forecasts will be skipped.
try:
    from prophet import Prophet
except Exception:
    try:
        from fbprophet import Prophet
    except Exception:
        Prophet = None
# Fallback: statsmodels ExponentialSmoothing for environments without Prophet
try:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
except Exception:
    ExponentialSmoothing = None

# --- Configuration ---
# DÃ©terminer le rÃ©pertoire de travail (oÃ¹ se trouve le script)
script_dir = Path(__file__).parent.resolve()
project_root = script_dir.parents[1]
SYNTHETIC_DIR = project_root / 'donnees' / 'synthetiques'
STATIC_DASHBOARD_DIR = project_root / 'presentation' / 'dashboards_statiques'
LOCAL_OUTPUT_DIR = project_root / 'sorties_intermediaires' / 'local'
NATIONAL_OUTPUT_DIR = project_root / 'sorties_intermediaires' / 'national'
INTERNATIONAL_OUTPUT_DIR = project_root / 'sorties_intermediaires' / 'international'
FORECAST_OUTPUT_DIR = project_root / 'sorties_intermediaires' / 'previsions'
REGIONAL_OUTPUT_DIR = project_root / 'sorties_intermediaires' / 'regional'
for _dir in [STATIC_DASHBOARD_DIR, LOCAL_OUTPUT_DIR, NATIONAL_OUTPUT_DIR, INTERNATIONAL_OUTPUT_DIR, FORECAST_OUTPUT_DIR, REGIONAL_OUTPUT_DIR]:
    _dir.mkdir(parents=True, exist_ok=True)

# --- Helpers ---
def ensure_bool(s):
    if s.dtype == bool:
        return s
    return s.astype(str).str.lower().isin(['true','1','oui','yes'])

def wilson_ci(k, n, z=1.96):
    if n == 0:
        return (np.nan, np.nan)
    phat = k/n
    denom = 1 + z**2/n
    center = (phat + z**2/(2*n)) / denom
    half = (z*np.sqrt(phat*(1-phat)/n + z**2/(4*n**2))) / denom
    return (max(0, center-half), min(1, center+half))

# --- Load data ---
# Robustly locate the synthetic input CSV across the reorganized data layer.
candidates = [
    SYNTHETIC_DIR / 'exports_script_extraction' / 'donnees_synthetiques_flat.csv',
    SYNTHETIC_DIR / 'exports_racine_crf_mpox' / 'donnees_synthetiques_flat.csv',
]
candidates = [p for p in candidates if p.exists()]
data_path = None
if candidates:
    # prefer a CSV that contains season/region columns if possible
    for p in candidates:
        try:
            cols = pd.read_csv(p, nrows=0).columns.tolist()
            if 'region' in cols or 'saison_pluvieuse_level' in cols:
                data_path = p
                break
        except Exception:
            continue
    if data_path is None:
        data_path = candidates[0]

if data_path is None or not data_path.exists():
    print(f"ERREUR: Fichier non trouve: donnees_synthetiques_flat.csv (recherches sous {project_root})")
    print(f"Repertoire courant: {os.getcwd()}")
    print(f"Fichiers disponibles:")
    for p in project_root.rglob('*donnees_synthetiques*'):
        print(f"  - {p}")
    exit(1)

print(f"Chargement du fichier synthÃ©tique: {data_path}")
df = pd.read_csv(data_path)

# Normalize booleans
bool_cols = ['pcr_any_positif','pcr_lesion_positif','pcr_oropharynx_positif',
             'vaccin_variole','vaccin_mva','vaccin_varicelle',
             'antecedent_voyage','voyage_zone_epidemie','contact_cas_confirm_suspect',
             'vih_charge_supprimee','vih_non_supprimee','vih_sans_arv',
             'severe']  # Ajout de 'severe' si prÃ©sent
for c in bool_cols:
    if c in df.columns: df[c] = ensure_bool(df[c])

# Dates
date_cols = ['date_premiers_symptomes','pcr_lesionnaire_date','pcr_oropharynge_date']
for c in date_cols:
    if c in df.columns: df[c+'_dt'] = pd.to_datetime(df[c], dayfirst=True, errors='coerce')

# Derived variables (amÃ©liorÃ© pour robustesse)
if 'delai_symptomes_vers_pcr_jours' not in df.columns and {'pcr_lesionnaire_date_dt','date_premiers_symptomes_dt'} <= set(df.columns):
    df['delai_symptomes_vers_pcr_jours'] = (df['pcr_lesionnaire_date_dt'] - df['date_premiers_symptomes_dt']).dt.days.clip(lower=0)

if 'ct_value_num' not in df.columns:
    c1 = pd.to_numeric(df.get('pcr_lesionnaire_ct_value'), errors='coerce')
    c2 = pd.to_numeric(df.get('pcr_oropharynge_ct_value'), errors='coerce')
    df['ct_value_num'] = c1.combine_first(c2)

symptom_cols = [c for c in df.columns if c.endswith('_present')]
if 'nb_symptomes' not in df.columns and symptom_cols:
    df['nb_symptomes'] = df[symptom_cols].sum(axis=1, numeric_only=True)

if 'vih_statut' not in df.columns:
    def vih_status(row):
        if row.get('vih_charge_supprimee', False): return 'VIH_supp'
        if row.get('vih_non_supprimee', False): return 'VIH_non_supp'
        if row.get('vih_sans_arv', False): return 'VIH_pas_ARV'
        return 'VIH_neg_inconnu'
    df['vih_statut'] = df.apply(vih_status, axis=1)

if 'nb_localisations_lesions' not in df.columns and 'localisations' in df.columns:
    df['nb_localisations_lesions'] = df['localisations'].fillna('').apply(lambda s: 0 if s=='' else s.count(';')+1)

# SÃ©vÃ©ritÃ© (heuristique amÃ©liorÃ©e: inclut nb localisations pour proxy d'Ã©tendue)
if 'severe' not in df.columns:
    vih_any = df[['vih_charge_supprimee','vih_non_supprimee','vih_sans_arv']].any(axis=1)
    df['severe'] = ((df['nb_symptomes']>=5) | ((df['nb_symptomes']>=4) & vih_any) | ((df['nb_localisations_lesions']>=3) & (df['nb_symptomes']>=3)))

# Vaccin type & mobilitÃ© groupe (amÃ©liorÃ© pour inclure zone Ã©pidÃ©mie)
def vaccine_type(row):
    v = []
    if row.get('vaccin_variole', False): v.append('Variole')
    if row.get('vaccin_mva', False): v.append('MVA')
    if row.get('vaccin_varicelle', False): v.append('Varicelle')
    if not v: return 'Aucun'
    return '+'.join(sorted(v))
df['vaccin_type'] = df.apply(vaccine_type, axis=1)

def mob_group(row):
    a = row.get('antecedent_voyage', False)
    z = row.get('voyage_zone_epidemie', False)
    c = row.get('contact_cas_confirm_suspect', False)
    if not a and not c: return 'Aucun'
    if a and z and not c: return 'Voyage en zone Ã©pidÃ©mie'
    if a and not z and not c: return 'Voyage hors zone'
    if c and not a: return 'Contact'
    return 'Voyage (Â±zone) + Contact'
df['mobilite_groupe'] = df.apply(mob_group, axis=1)

# Bins (amÃ©liorÃ© pour Ã©pidÃ©mie: age bins OMS-like, dÃ©lai bins pour dÃ©tection prÃ©coce)
df['delai_bin'] = pd.cut(df['delai_symptomes_vers_pcr_jours'], bins=[-0.1,3,7,14,np.inf], labels=['0-3','4-7','8-14','>=15'])  # Focus dÃ©tection rapide
df['age_bin']   = pd.cut(df['age'], bins=[0,4,17,29,44,59,200], labels=['0-4','5-17','18-29','30-44','45-59','60+'])

# Charge virale cat si pas dÃ©jÃ 
if 'charge_virale_cat' not in df.columns and 'ct_value_num' in df.columns:
    bins = [0,20,30,np.inf]
    labels=['haute','moyenne','basse']
    df['charge_virale_cat'] = pd.cut(df['ct_value_num'], bins=bins, labels=labels)

# --- Plot settings ---
sns.set(style='whitegrid', context='talk')
outdir = STATIC_DASHBOARD_DIR
outdir.mkdir(exist_ok=True)

def savefig(name, fig=None):
    if fig is None: fig = plt.gcf()
    fig.tight_layout()
    fpath = outdir / name
    fig.savefig(fpath, dpi=140, bbox_inches='tight')
    print(f"[OK] Graphique cree: {fpath.name}")
    plt.close(fig)

# 1) Incidence & positivitÃ© par semaine (pertinent pour surveillance Ã©pidÃ©mie)
if 'pcr_lesionnaire_date_dt' in df.columns and 'pcr_any_positif' in df.columns:
    tmp = df.copy()
    tmp['semaine'] = tmp['pcr_lesionnaire_date_dt'].dt.to_period('W').astype(str)
    # compute a week start date (pd.Timestamp) for time series modelling
    # Guard against NaT periods (apply lambda that returns pd.NaT when period is missing)
    periods = tmp['pcr_lesionnaire_date_dt'].dt.to_period('W')
    tmp['week_start'] = periods.apply(lambda r: r.start_time if pd.notna(r) else pd.NaT)
    g = tmp.groupby('week_start').agg(n=('pcr_any_positif','size'), pos=('pcr_any_positif','sum')).reset_index()
    g['positivite'] = g['pos']/g['n']
    # recreate human-readable week label used by plotting code
    g['semaine'] = g['week_start'].dt.date.astype(str) + '/' + (g['week_start'] + pd.Timedelta(days=6)).dt.date.astype(str)
    ci = g.apply(lambda r: wilson_ci(r['pos'], r['n']), axis=1)
    g['ci_low']  = [c[0] for c in ci]
    g['ci_high'] = [c[1] for c in ci]
    fig, ax1 = plt.subplots(figsize=(12,7)); ax2 = ax1.twinx()
    ax1.bar(g['semaine'], g['n'], color='#9ecae1', alpha=0.7, label='TestÃ©s (n)')
    ax2.plot(g['semaine'], g['positivite']*100, color='#e6550d', marker='o', label='PositivitÃ© (%)')
    ax2.fill_between(g['semaine'], g['ci_low']*100, g['ci_high']*100, color='#e6550d', alpha=0.15, linewidth=0)
    ax1.set_xlabel('Semaine'); ax1.set_ylabel('Nombre testÃ©s'); ax2.set_ylabel('PositivitÃ© (%)')
    ax1.set_title('Surveillance: Volume testÃ© et positivitÃ© par semaine'); ax1.tick_params(axis='x', rotation=45)
    ax1.legend(loc='upper left'); ax2.legend(loc='upper right')
    savefig('01_surveillance_incidence_positivite_semaine.png')

    # --- Forecasting (Phase 1) ---
    # Use Prophet to forecast incidence (counts) and positivity (proportion) if available
    min_weeks_for_forecast = 4  # lowered minimum weeks required for forecasting
    forecast_periods = 8  # weeks
    try:
        if Prophet is not None and len(g) >= min_weeks_for_forecast:
            # Prophet path (unchanged)
            df_inc = g[['week_start','n']].rename(columns={'week_start':'ds','n':'y'}).sort_values('ds')
            m_inc = Prophet(interval_width=0.95)
            m_inc.fit(df_inc)
            future_inc = m_inc.make_future_dataframe(periods=forecast_periods, freq='W')
            fc_inc = m_inc.predict(future_inc)

            df_pos = g[['week_start','positivite']].rename(columns={'week_start':'ds','positivite':'y'}).sort_values('ds')
            m_pos = Prophet(interval_width=0.95)
            m_pos.fit(df_pos)
            future_pos = m_pos.make_future_dataframe(periods=forecast_periods, freq='W')
            fc_pos = m_pos.predict(future_pos)

            fc_out = pd.DataFrame({
                'ds': fc_inc['ds'],
                'forecast_incidence': fc_inc['yhat'].values,
                'inc_low': fc_inc['yhat_lower'].values,
                'inc_high': fc_inc['yhat_upper'].values,
            })
            fc_out = fc_out.merge(
                pd.DataFrame({'ds': fc_pos['ds'], 'forecast_positivity': fc_pos['yhat'].values, 'pos_low': fc_pos['yhat_lower'].values, 'pos_high': fc_pos['yhat_upper'].values}),
                on='ds', how='left'
            )

        elif Prophet is None and ExponentialSmoothing is not None and len(g) >= min_weeks_for_forecast:
            # Fallback forecasting using Exponential Smoothing
            vals_inc = g.sort_values('week_start')['n'].astype(float).values
            vals_pos = g.sort_values('week_start')['positivite'].astype(float).fillna(0).values
            # Fit simple additive trend models (no seasonality assumed)
            try:
                m_inc = ExponentialSmoothing(vals_inc, trend='add', seasonal=None, initialization_method='estimated').fit(optimized=True)
                pred_inc = m_inc.predict(start=0, end=len(vals_inc)-1+forecast_periods)
                resid_inc = m_inc.fittedvalues - vals_inc
                se_inc = np.nanstd(resid_inc) if len(resid_inc)>1 else np.nan
            except Exception:
                pred_inc = np.concatenate([vals_inc, np.repeat(vals_inc.mean(), forecast_periods)])
                se_inc = np.nanstd(vals_inc - vals_inc.mean())

            try:
                m_pos = ExponentialSmoothing(vals_pos, trend='add', seasonal=None, initialization_method='estimated').fit(optimized=True)
                pred_pos = m_pos.predict(start=0, end=len(vals_pos)-1+forecast_periods)
                resid_pos = m_pos.fittedvalues - vals_pos
                se_pos = np.nanstd(resid_pos) if len(resid_pos)>1 else np.nan
            except Exception:
                pred_pos = np.concatenate([vals_pos, np.repeat(vals_pos.mean(), forecast_periods)])
                se_pos = np.nanstd(vals_pos - vals_pos.mean())

            # Build output dates
            start = g['week_start'].sort_values().iloc[0]
            periods_total = len(vals_inc) + forecast_periods
            future_ds = pd.date_range(start=start, periods=periods_total, freq='W')

            fc_out = pd.DataFrame({
                'ds': future_ds,
                'forecast_incidence': np.round(pred_inc, 3),
                'inc_low': np.round(pred_inc - 1.96 * (se_inc if not np.isnan(se_inc) else 0), 3),
                'inc_high': np.round(pred_inc + 1.96 * (se_inc if not np.isnan(se_inc) else 0), 3),
                'forecast_positivity': np.clip(pred_pos, 0, 1),
            })
            fc_out['pos_low'] = np.clip(fc_out['forecast_positivity'] - 1.96 * (se_pos if not np.isnan(se_pos) else 0), 0, 1)
            fc_out['pos_high'] = np.clip(fc_out['forecast_positivity'] + 1.96 * (se_pos if not np.isnan(se_pos) else 0), 0, 1)

        else:
            if len(g) < min_weeks_for_forecast:
                print(f'DonnÃ©es insuffisantes pour prÃ©visions (moins de {min_weeks_for_forecast} semaines).')
                fc_out = None
            else:
                print('Aucun moteur de prÃ©vision disponible (installer `prophet` ou `statsmodels`).')
                fc_out = None

        # Common postprocessing when fc_out was created
        if fc_out is not None:
            fc_out['semaine'] = fc_out['ds'].dt.date.astype(str) + '/' + (fc_out['ds'] + pd.Timedelta(days=6)).dt.date.astype(str)
            last_obs = g.sort_values('week_start').iloc[-1]
            match = fc_out[fc_out['ds'] == last_obs['week_start']]
            if not match.empty:
                pred_pos = float(match['forecast_positivity'].iloc[0])
                obs_pos = float(last_obs['positivite']) if last_obs['positivite'] is not None else np.nan
                ecart_pct = (obs_pos - pred_pos) / pred_pos * 100 if pred_pos != 0 else np.nan
            else:
                ecart_pct = np.nan

            def alert_level(p):
                try:
                    p = float(p)
                except Exception:
                    return ('NA','gray','')
                if p > 0.5:
                    return ('Critique','black','ðŸš¨')
                if p > 0.3:
                    return ('Danger','red','ðŸ›‘')
                if p > 0.15:
                    return ('Vigilance','orange','âš ï¸')
                return ('RAS','green','âœ…')

            recent_level = alert_level(last_obs['positivite'])
            fc_out['ecart_%_last_obs_vs_pred_pos'] = ecart_pct
            fc_out['last_obs_positivity'] = last_obs['positivite']
            fc_out['last_obs_alert_label'] = recent_level[0]
            fc_out['last_obs_alert_color'] = recent_level[1]
            fc_out['last_obs_alert_emoji'] = recent_level[2]

            FORECAST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            fc_out.to_csv(FORECAST_OUTPUT_DIR / 'national_forecast.csv', index=False)
            print(f"[OK] Previsions nationales generees: {FORECAST_OUTPUT_DIR / 'national_forecast.csv'}")
            # --- Generate forecast plots (incidence and positivity) and save PNGs ---
            try:
                # Merge observed g (if present) with fc_out on ds / week_start
                obs = g[['week_start','n','positivite']].rename(columns={'week_start':'ds'}) if 'g' in locals() else None
                df_fc = fc_out.copy()
                df_fc['ds'] = pd.to_datetime(df_fc['ds'])

                # Incidence plot: observed bars + forecast line + CI
                try:
                    fig, ax1 = plt.subplots(figsize=(12,7)); ax2 = ax1.twinx()
                    if obs is not None:
                        obs_sorted = obs.sort_values('ds')
                        ax1.bar(obs_sorted['ds'].dt.date.astype(str), obs_sorted['n'], color='#9ecae1', alpha=0.7, label='TestÃ©s (n)')
                    ax2.plot(df_fc['ds'].dt.date.astype(str), df_fc['forecast_incidence'], color='#3182bd', marker='o', label='PrÃ©vision incidence')
                    if 'inc_low' in df_fc.columns and 'inc_high' in df_fc.columns:
                        ax2.fill_between(df_fc['ds'].dt.date.astype(str), df_fc['inc_low'], df_fc['inc_high'], color='#3182bd', alpha=0.15)
                    ax1.set_xlabel('Semaine'); ax1.set_ylabel('Nombre testÃ©s'); ax2.set_ylabel('PrÃ©vision incidence')
                    ax1.set_title('PrÃ©vision: Incidence hebdomadaire (observÃ© + prÃ©vision)')
                    ax1.tick_params(axis='x', rotation=45)
                    ax1.legend(loc='upper left'); ax2.legend(loc='upper right')
                    savefig('15_forecast_incidence.png')
                except Exception as _e:
                    print('Warning: cannot create incidence forecast plot:', _e)

                # Positivity plot: observed positivity (%) + forecast positivity (%) + CI
                try:
                    fig, ax = plt.subplots(figsize=(12,7))
                    if obs is not None:
                        obs_sorted = obs.sort_values('ds')
                        ax.plot(obs_sorted['ds'].dt.date.astype(str), obs_sorted['positivite']*100, color='#de2d26', marker='o', label='ObservÃ© (%)')
                    ax.plot(df_fc['ds'].dt.date.astype(str), df_fc['forecast_positivity']*100, color='#e6550d', linestyle='--', marker='o', label='PrÃ©vision (%)')
                    if 'pos_low' in df_fc.columns and 'pos_high' in df_fc.columns:
                        ax.fill_between(df_fc['ds'].dt.date.astype(str), df_fc['pos_low']*100, df_fc['pos_high']*100, color='#e6550d', alpha=0.12)
                    ax.set_xlabel('Semaine'); ax.set_ylabel('PositivitÃ© (%)'); ax.set_title('PrÃ©vision: PositivitÃ© hebdomadaire (observÃ© + prÃ©vision)')
                    ax.tick_params(axis='x', rotation=45)
                    ax.legend()
                    savefig('15_forecast_positivity.png')
                except Exception as _e:
                    print('Warning: cannot create positivity forecast plot:', _e)
            except Exception as _e:
                print('Warning: could not produce forecast PNGs:', _e)
    except Exception as _e:
        print('Erreur lors de la gÃ©nÃ©ration des prÃ©visions:', _e)

# 2) PositivitÃ© par type dâ€™Ã©chantillon (pertinent pour optimisation diagnostic)
if {'pcr_lesion_positif','pcr_oropharynx_positif'} <= set(df.columns):
    data = []
    for lab, col in [('LÃ©sion','pcr_lesion_positif'),('Oropharynx','pcr_oropharynx_positif')]:
        s = df[col].dropna(); n = s.shape[0]; k = int(s.sum()); p = k/n if n>0 else np.nan
        lo, hi = wilson_ci(k,n)
        data.append({'type_echantillon':lab,'n':n,'positivite':p,'low':lo,'high':hi})
    gg = pd.DataFrame(data)
    fig, ax = plt.subplots(figsize=(8,6))
    sns.barplot(data=gg, x='type_echantillon', y='positivite', hue='type_echantillon', dodge=False, palette='Blues', legend=False, ax=ax)
    y = gg['positivite'].values
    yerr_low = (y - gg['low'].values).clip(min=0)
    yerr_high = (gg['high'].values - y).clip(min=0)
    ax.errorbar(x=np.arange(len(gg)), y=y, yerr=[yerr_low, yerr_high], fmt='none', ecolor='black', capsize=5)
    ax.set_ylim(0,1); ax.set_ylabel('PositivitÃ©'); ax.set_xlabel('Type dâ€™Ã©chantillon')
    ax.set_title('Diagnostic: PositivitÃ© PCR par type dâ€™Ã©chantillon')
    ax.set_yticklabels(['{:.0f}%'.format(t*100) for t in ax.get_yticks()])
    for i,row in gg.iterrows(): ax.text(i, row['positivite']+0.03, f"n={row['n']}", ha='center', va='bottom')
    savefig('02_diagnostic_positivite_par_type.png')

# 3) Ct vs dÃ©lai (pertinent pour fenÃªtre de dÃ©tection/infectiositÃ©)
if {'ct_value_num','delai_symptomes_vers_pcr_jours','pcr_any_positif'} <= set(df.columns):
    pos = df[df['pcr_any_positif'] & df['ct_value_num'].notna() & df['delai_symptomes_vers_pcr_jours'].notna()].copy()
    if not pos.empty:
        fig, ax = plt.subplots(figsize=(10,6))
        sns.scatterplot(data=pos, x='delai_symptomes_vers_pcr_jours', y='ct_value_num', color='#e6550d', alpha=0.7, ax=ax)
        ax.set_xlabel('DÃ©lai symptÃ´mes â†’ PCR (jours)'); ax.set_ylabel('Ct'); ax.set_title('InfectiositÃ©: Ct vs dÃ©lai (PCR positives)')
        savefig('03a_infectiosite_ct_vs_delai_scatter.png')

        pos['delai_bin'] = pd.cut(pos['delai_symptomes_vers_pcr_jours'], bins=[-0.1,3,7,14,np.inf], labels=['0-3','4-7','8-14','>=15'])
        fig, ax = plt.subplots(figsize=(9,6))
        sns.boxplot(data=pos, x='delai_bin', y='ct_value_num', palette='Oranges', ax=ax)
        ax.set_xlabel('Tranche de dÃ©lai (jours)'); ax.set_ylabel('Ct'); ax.set_title('InfectiositÃ©: Ct par tranche de dÃ©lai (PCR positives)')
        savefig('03b_infectiosite_ct_vs_delai_box.png')

# 4) Nb symptÃ´mes par statut PCR (pertinent pour identification cas suspects)
if {'nb_symptomes','pcr_any_positif'} <= set(df.columns):
    fig, ax = plt.subplots(figsize=(8,6))
    sns.boxplot(data=df, x='pcr_any_positif', y='nb_symptomes', palette='Set2', ax=ax)
    ax.set_xlabel('PCR positive ?'); ax.set_ylabel('Nombre de symptÃ´mes'); ax.set_title('Identification: Nombre de symptÃ´mes par statut PCR')
    ax.set_xticklabels(['Non','Oui'])
    savefig('04_identification_nb_symptomes_par_statut.png')

# 5) SÃ©vÃ©ritÃ© par statut VIH (pertinent pour groupes Ã  risque)
if {'vih_statut','severe'} <= set(df.columns):
    base = df.groupby('vih_statut')['severe'].value_counts(normalize=True).rename('prop').reset_index()
    base['prop_pct'] = base['prop']*100
    order = ['VIH_neg_inconnu','VIH_supp','VIH_non_supp','VIH_pas_ARV']
    fig, ax = plt.subplots(figsize=(10,6))
    bottom = np.zeros(len(order))
    for val, color in [(False,'#9ecae1'),(True,'#de2d26')]:
        vals = []
        for k in order:
            r = base[(base['vih_statut']==k) & (base['severe']==val)]['prop_pct']
            vals.append(float(r.iloc[0]) if len(r)>0 else 0)
        ax.bar(order, vals, bottom=bottom, color=color, label=('SÃ©vÃ©ritÃ© basse' if not val else 'SÃ©vÃ©ritÃ© haute'))
        bottom += np.array(vals)
    ax.set_ylabel('Proportion (%)'); ax.set_xlabel('Statut VIH'); ax.set_title('Risques: SÃ©vÃ©ritÃ© clinique par statut VIH'); ax.legend()
    savefig('05_risques_severite_par_vih.png')

# 6) PositivitÃ© selon statut vaccinal (pertinent pour efficacitÃ© vaccinale/prÃ©vention)
if {'vaccin_type','pcr_any_positif'} <= set(df.columns):
    vt = df.groupby('vaccin_type').agg(n=('pcr_any_positif','size'), pos=('pcr_any_positif','sum')).reset_index()
    vt['p'] = vt['pos']/vt['n']
    ci = vt.apply(lambda r: wilson_ci(r['pos'], r['n']), axis=1)
    vt['low'] = [c[0] for c in ci]; vt['high'] = [c[1] for c in ci]
    order = vt.sort_values('p', ascending=False)['vaccin_type'].tolist()
    vt_ord = vt.set_index('vaccin_type').loc[order]
    fig, ax = plt.subplots(figsize=(12,6))
    sns.barplot(data=vt_ord.reset_index(), x='vaccin_type', y='p', hue='vaccin_type', dodge=False, palette='Greens', legend=False, ax=ax)
    y = vt_ord['p'].values
    yerr_low = (y - vt_ord['low'].values).clip(min=0)
    yerr_high = (vt_ord['high'].values - y).clip(min=0)
    ax.errorbar(x=np.arange(len(vt_ord)), y=y, yerr=[yerr_low, yerr_high], fmt='none', ecolor='black', capsize=5)
    ax.set_ylim(0,1); ax.set_ylabel('PositivitÃ©'); ax.set_xlabel('Type vaccinal')
    ax.set_title('PrÃ©vention: PositivitÃ© PCR selon statut vaccinal')
    ax.set_yticklabels(['{:.0f}%'.format(t*100) for t in ax.get_yticks()])
    for i,(pval,nval) in enumerate(zip(vt_ord['p'].values, vt_ord['n'].values)):
        ax.text(i, pval+0.03, f"n={int(nval)}", ha='center')
    ax.tick_params(axis='x', rotation=45)
    savefig('06_prevention_positivite_par_vaccin.png')

# 7) Distribution de lâ€™Ã¢ge selon statut PCR (pertinent pour dÃ©mographie/transmission)
if {'age','pcr_any_positif'} <= set(df.columns):
    fig, ax = plt.subplots(figsize=(8,6))
    sns.violinplot(data=df, x='pcr_any_positif', y='age', palette='Pastel1', inner='box', ax=ax)
    ax.set_xlabel('PCR positive ?'); ax.set_xticklabels(['Non','Oui']); ax.set_ylabel('Ã‚ge (ans)')
    ax.set_title('DÃ©mographie: Distribution de lâ€™Ã¢ge selon statut PCR')
    savefig('07_demographie_age_par_statut.png')

# 8) Indices prÃ©-analytiques vs positivitÃ© (pertinent pour qualitÃ© diagnostic)
pre_idx = ['index_hemolytique','indice_lipemique','indice_icterique']
exist_idx = [c for c in pre_idx if c in df.columns]
if exist_idx and 'pcr_any_positif' in df.columns:
    fig, axes = plt.subplots(1, len(exist_idx), figsize=(7*len(exist_idx),6), sharey=True)
    if len(exist_idx) == 1: axes = [axes]
    for ax, col in zip(axes, exist_idx):
        tab = df.groupby(col)['pcr_any_positif'].agg(['mean','count','sum']).reset_index()
        tab['p'] = tab['mean']
        order = ['-','+','++','+++','++++']
        ord_present = [o for o in order if o in tab[col].unique()]
        sns.barplot(data=tab, x=col, y='p', ax=ax, order=ord_present, hue=col, dodge=False, palette='YlGn', legend=False)
        ax.set_ylim(0,1); ax.set_title(f'PositivitÃ© vs {col.replace("_"," ").title()}'); ax.set_ylabel('PositivitÃ©')
        ax.set_yticklabels(['{:.0f}%'.format(y*100) for y in ax.get_yticks()]); ax.set_xlabel(col.replace('_',' ').title())
    plt.suptitle('QualitÃ© diagnostic: Impact indices prÃ©-analytiques', y=1.03, fontsize=16)
    savefig('08_qualite_indices_preanalytiques.png')

# 9) Ã‰tendue des lÃ©sions (pertinent pour infectiositÃ©/transmission)
if 'nb_localisations_lesions' in df.columns:
    cats = pd.cut(df['nb_localisations_lesions'], bins=[0,1,2,3,np.inf], labels=['1','2','3','>=4'])  # Plus fin
    tab = cats.value_counts().reindex(['1','2','3','>=4']).fillna(0)
    fig, ax = plt.subplots(figsize=(7,6))
    sns.barplot(x=tab.index, y=tab.values, hue=tab.index, dodge=False, palette='Purples', legend=False, ax=ax)
    ax.set_xlabel('Nombre de localisations de lÃ©sions'); ax.set_ylabel('Nombre de patients'); ax.set_title('InfectiositÃ©: Ã‰tendue des lÃ©sions')
    for i,v in enumerate(tab.values): ax.text(i, v+0.5, f'n={int(v)}', ha='center')
    savefig('09_infectiosite_nb_localisations_lesions.png')

# 10) NOUVEAU: PositivitÃ© par groupe de mobilitÃ© (pertinent pour transmission/exposition)
if {'mobilite_groupe','pcr_any_positif'} <= set(df.columns):
    mg = df.groupby('mobilite_groupe').agg(n=('pcr_any_positif','size'), pos=('pcr_any_positif','sum')).reset_index()
    mg['p'] = mg['pos']/mg['n']
    ci = mg.apply(lambda r: wilson_ci(r['pos'], r['n']), axis=1)
    mg['low'] = [c[0] for c in ci]; mg['high'] = [c[1] for c in ci]
    order = ['Aucun','Voyage hors zone','Contact','Voyage en zone Ã©pidÃ©mie','Voyage (Â±zone) + Contact']
    ord_present = [o for o in order if o in mg['mobilite_groupe'].unique()]
    mg_ord = mg.set_index('mobilite_groupe').loc[ord_present]
    fig, ax = plt.subplots(figsize=(12,6))
    sns.barplot(data=mg_ord.reset_index(), x='mobilite_groupe', y='p', hue='mobilite_groupe', dodge=False, palette='Reds', legend=False, ax=ax)
    y = mg_ord['p'].values
    yerr_low = (y - mg_ord['low'].values).clip(min=0)
    yerr_high = (mg_ord['high'].values - y).clip(min=0)
    ax.errorbar(x=np.arange(len(mg_ord)), y=y, yerr=[yerr_low, yerr_high], fmt='none', ecolor='black', capsize=5)
    ax.set_ylim(0,1); ax.set_ylabel('PositivitÃ©'); ax.set_xlabel('Groupe de mobilitÃ©/exposition')
    ax.set_title('Transmission: PositivitÃ© PCR par mobilitÃ© et exposition')
    ax.set_yticklabels(['{:.0f}%'.format(t*100) for t in ax.get_yticks()])
    for i,(pval,nval) in enumerate(zip(mg_ord['p'].values, mg_ord['n'].values)):
        ax.text(i, pval+0.03, f"n={int(nval)}", ha='center')
    ax.tick_params(axis='x', rotation=45)
    savefig('10_transmission_positivite_par_mobilite.png')

# 11) NOUVEAU: PositivitÃ© par tranche d'Ã¢ge (pertinent pour ciblage prÃ©vention)
if {'age_bin','pcr_any_positif'} <= set(df.columns):
    ab = df.groupby('age_bin').agg(n=('pcr_any_positif','size'), pos=('pcr_any_positif','sum')).reset_index()
    ab['p'] = ab['pos']/ab['n']
    ci = ab.apply(lambda r: wilson_ci(r['pos'], r['n']), axis=1)
    ab['low'] = [c[0] for c in ci]; ab['high'] = [c[1] for c in ci]
    order = ['0-4','5-17','18-29','30-44','45-59','60+']
    # Filtrer pour garder seulement les tranches existantes
    order_present = [o for o in order if o in ab['age_bin'].unique()]
    ab_ord = ab.set_index('age_bin').loc[order_present] if order_present else ab
    if not ab_ord.empty:
        fig, ax = plt.subplots(figsize=(10,6))
        sns.barplot(data=ab_ord.reset_index(), x='age_bin', y='p', hue='age_bin', dodge=False, palette='Blues', legend=False, ax=ax)
        y = ab_ord['p'].values
        yerr_low = (y - ab_ord['low'].values).clip(min=0)
        yerr_high = (ab_ord['high'].values - y).clip(min=0)
        ax.errorbar(x=np.arange(len(ab_ord)), y=y, yerr=[yerr_low, yerr_high], fmt='none', ecolor='black', capsize=5)
        ax.set_ylim(0,1); ax.set_ylabel('Positivite'); ax.set_xlabel('Tranche d\'age')
        ax.set_title('Ciblage: Positivite PCR par tranche d\'age')
        ax.set_yticklabels(['{:.0f}%'.format(t*100) for t in ax.get_yticks()])
        for i,(pval,nval) in enumerate(zip(ab_ord['p'].values, ab_ord['n'].values)):
            ax.text(i, pval+0.03, f"n={int(nval)}", ha='center')
        savefig('11_ciblage_positivite_par_age.png')


# 12) NOUVEAU: SÃ©vÃ©ritÃ© par tranche d'Ã¢ge (pertinent pour priorisation soins/groupes vulnÃ©rables)
if {'age_bin','severe'} <= set(df.columns):
    sab = df.groupby('age_bin')['severe'].agg(['mean','count','sum']).reset_index()
    sab['p'] = sab['mean']
    ci = sab.apply(lambda r: wilson_ci(r['sum'], r['count']), axis=1)
    sab['low'] = [c[0] for c in ci]; sab['high'] = [c[1] for c in ci]
    order = ['0-4','5-17','18-29','30-44','45-59','60+']
    # Use reindex to avoid KeyError when some age bins are absent
    sab_ord = sab.set_index('age_bin').reindex(order)
    fig, ax = plt.subplots(figsize=(10,6))
    sns.barplot(data=sab_ord.reset_index(), x='age_bin', y='p', hue='age_bin', dodge=False, palette='OrRd', legend=False, ax=ax)
    y = sab_ord['p'].values
    yerr_low = (y - sab_ord['low'].values).clip(min=0)
    yerr_high = (sab_ord['high'].values - y).clip(min=0)
    ax.errorbar(x=np.arange(len(sab_ord)), y=y, yerr=[yerr_low, yerr_high], fmt='none', ecolor='black', capsize=5)
    ax.set_ylim(0,1); ax.set_ylabel('Proportion sÃ©vÃ¨re'); ax.set_xlabel('Tranche dâ€™Ã¢ge')
    ax.set_title('VulnÃ©rabilitÃ©s: SÃ©vÃ©ritÃ© par tranche dâ€™Ã¢ge')
    ax.set_yticklabels(['{:.0f}%'.format(t*100) for t in ax.get_yticks()])
    for i,(pval,nval) in enumerate(zip(sab_ord['p'].values, sab_ord['count'].values)):
        display_p = 0 if pd.isna(pval) else pval
        display_n = int(nval) if pd.notna(nval) else 0
        ax.text(i, display_p+0.03, f"n={display_n}", ha='center')
    savefig('12_vulnerabilites_severite_par_age.png')

# 13) NOUVEAU: Nb localisations par charge virale cat (pertinent pour potentiel de transmission)
if {'nb_localisations_lesions','charge_virale_cat'} <= set(df.columns):
    pos_les = df[df['pcr_any_positif'] & df['ct_value_num'].notna()].copy()
    if not pos_les.empty:
        fig, ax = plt.subplots(figsize=(9,6))
        sns.boxplot(data=pos_les, x='charge_virale_cat', y='nb_localisations_lesions', palette='YlOrRd', ax=ax, order=['haute','moyenne','basse'])
        ax.set_xlabel('CatÃ©gorie de charge virale (basÃ©e sur Ct)'); ax.set_ylabel('Nombre de localisations de lÃ©sions')
        ax.set_title('Transmission: Ã‰tendue lÃ©sions par charge virale (PCR positives)')
        savefig('13_transmission_nb_localisations_par_charge_virale.png')

# 14) NOUVEAU: PositivitÃ© par sexe (pertinent pour dÃ©mographie/genre-spÃ©cifique prÃ©vention)
if {'sexe','pcr_any_positif'} <= set(df.columns):
    sex_pos = df.groupby('sexe').agg(n=('pcr_any_positif','size'), pos=('pcr_any_positif','sum')).reset_index()
    sex_pos['p'] = sex_pos['pos']/sex_pos['n']
    ci = sex_pos.apply(lambda r: wilson_ci(r['pos'], r['n']), axis=1)
    sex_pos['low'] = [c[0] for c in ci]; sex_pos['high'] = [c[1] for c in ci]
    order = ['H','F']
    sex_ord = sex_pos.set_index('sexe').loc[order]
    fig, ax = plt.subplots(figsize=(7,6))
    sns.barplot(data=sex_ord.reset_index(), x='sexe', y='p', hue='sexe', dodge=False, palette='Set3', legend=False, ax=ax)
    y = sex_ord['p'].values
    yerr_low = (y - sex_ord['low'].values).clip(min=0)
    yerr_high = (sex_ord['high'].values - y).clip(min=0)
    ax.errorbar(x=np.arange(len(sex_ord)), y=y, yerr=[yerr_low, yerr_high], fmt='none', ecolor='black', capsize=5)
    ax.set_ylim(0,1); ax.set_ylabel('PositivitÃ©'); ax.set_xlabel('Sexe')
    ax.set_title('DÃ©mographie: PositivitÃ© PCR par sexe')
    ax.set_yticklabels(['{:.0f}%'.format(t*100) for t in ax.get_yticks()])
    for i,(pval,nval) in enumerate(zip(sex_ord['p'].values, sex_ord['n'].values)):
        ax.text(i, pval+0.03, f"n={int(nval)}", ha='center')
    savefig('14_demographie_positivite_par_sexe.png')

# --- SaisonnalitÃ©: agrÃ©gats mensuels et par rÃ©gion (nouveaux visuels 16-18) ---
if 'pcr_lesionnaire_date_dt' in df.columns and 'pcr_any_positif' in df.columns:
    try:
        df_m = df.copy()
        df_m['month'] = df_m['pcr_lesionnaire_date_dt'].dt.to_period('M').dt.to_timestamp()
        monthly = df_m.groupby('month').agg(n_cases=('pcr_any_positif','size'), n_pos=('pcr_any_positif','sum')).reset_index()
        monthly['positivity'] = monthly['n_pos'] / monthly['n_cases']
        # Seasonal level (0..1) per month using same formula as generator
        def season_level_date(d):
            m = d.month
            angle = 2 * np.pi * ((m - 8) / 12.0)
            return 0.5 * (1 + np.sin(-angle))
        monthly['saison_level'] = monthly['month'].apply(season_level_date)

        # Plot 16: incidence per month with Saison overlay
        fig, ax1 = plt.subplots(figsize=(12,7))
        ax2 = ax1.twinx()
        ax1.bar(monthly['month'].dt.strftime('%Y-%m'), monthly['n_cases'], color='#9ecae1', alpha=0.8, label='Cas (mensuel)')
        ax2.plot(monthly['month'].dt.strftime('%Y-%m'), monthly['saison_level'], color='#d62728', linestyle='--', marker='o', label='Niveau saison (0-1)')
        ax1.set_xlabel('Mois'); ax1.set_ylabel('Cas'); ax2.set_ylabel('Niveau saison')
        ax1.set_title('16 - Incidence mensuelle avec niveau saisonnier (saison pluvieuse)')
        ax1.tick_params(axis='x', rotation=45)
        ax1.legend(loc='upper left'); ax2.legend(loc='upper right')
        savefig('16_surveillance_incidence_par_mois_avec_saison.png')

        # Plot 17: heatmap positivitÃ© par region x month
        if 'region' in df_m.columns:
            reg = df_m.groupby([df_m['region'], df_m['month']]).agg(n=('pcr_any_positif','size'), pos=('pcr_any_positif','sum')).reset_index()
            reg['positivity'] = reg['pos'] / reg['n']
            pivot = reg.pivot(index='region', columns='month', values='positivity').fillna(0)
            # reorder columns
            pivot = pivot.sort_index(axis=1)
            fig, ax = plt.subplots(figsize=(14,6))
            sns.heatmap(pivot, cmap='Reds', vmin=0, vmax=max(0.1, pivot.values.max()), ax=ax, cbar_kws={'format':'%.0f%%'})
            ax.set_title('17 - Heatmap: positivitÃ© par rÃ©gion et mois')
            savefig('17_transmission_heatmap_positivite_par_region_saison.png')
            # save CSV for dashboard interactive heatmap
            REGIONAL_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            pivot.reset_index().to_csv(REGIONAL_OUTPUT_DIR / 'regional_positivity_monthly.csv', index=False)

        # Plot 18: severite par saison (True/False)
        if 'saison_pluvieuse' in df_m.columns and 'severe' in df_m.columns:
            sev = df_m.groupby('saison_pluvieuse').agg(n=('severe','size'), severe_count=('severe','sum')).reset_index()
            sev['severe_rate'] = sev['severe_count'] / sev['n']
            fig, ax = plt.subplots(figsize=(8,6))
            sns.barplot(data=sev, x='saison_pluvieuse', y='severe_rate', palette='OrRd', ax=ax)
            ax.set_xlabel('Saison pluvieuse'); ax.set_ylabel('Proportion sÃ©vÃ¨res')
            ax.set_title('18 - SÃ©vÃ©ritÃ© des cas selon saison pluvieuse')
            savefig('18_risques_severite_par_saison.png')
    except Exception as _e:
        print('Warning: could not create seasonal plots:', _e)

# --- Dashboard datasets: local / national / international ---

# Ensure output directory exists (re-uses `outdir` defined earlier)
_OUTPUT_DIR = outdir if 'outdir' in globals() else STATIC_DASHBOARD_DIR
_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _ensure_columns(df_, cols_defaults):
    """Ensure columns exist in df_; create with default if missing.
    cols_defaults: dict of col -> default scalar or callable(n) -> sequence
    Returns a shallow copy with guaranteed columns.
    """
    out = df_.copy()
    n = len(out)
    for col, default in cols_defaults.items():
        if col not in out.columns:
            if callable(default):
                out[col] = default(n)
            else:
                out[col] = [default] * n
    return out


def build_local_dataset(df):
    """LEVEL 1 â€” LOCAL DECISION MAKERS
    - Keep one row per case and all derived analytic variables
    - Remove laboratory QC indices and non-analytic metadata
    """
    local = df.copy()

    drop_candidates = [
        'index_hemolytique', 'indice_lipemique', 'indice_icterique',
        'source_file', 'file_path', 'ingest_time', 'created_at', 'updated_at',
        'raw_payload', 'meta'
    ]
    meta_prefixes = ('meta_', 'raw_', 'upload_', 'ingest_')

    to_drop = [c for c in drop_candidates if c in local.columns]
    to_drop += [c for c in local.columns if c.startswith(meta_prefixes)]
    to_drop = [c for c in to_drop if c in local.columns]
    if to_drop:
        local = local.drop(columns=to_drop)

    path = LOCAL_OUTPUT_DIR / 'data_local.csv'
    local.to_csv(path, index=False)
    return local


def build_national_dataset(df):
    """LEVEL 2 â€” NATIONAL DECISION MAKERS
    - Aggregate by semaine, sex (or `sexe`) and age_bin
    - Produce totals, positivity_rate, median_ct, mean_nb_symptomes,
      proportion_severe and distribution of charge_virale_cat
    """
    nat = df.copy()

    # Ensure semaine exists (compute from pcr_lesionnaire_date_dt if needed)
    # Ensure week_start and human-readable 'semaine' exist (consistent with forecasting)
    if 'week_start' not in nat.columns and 'pcr_lesionnaire_date_dt' in nat.columns:
        periods = nat['pcr_lesionnaire_date_dt'].dt.to_period('W')
        nat['week_start'] = periods.apply(lambda r: r.start_time if pd.notna(r) else pd.NaT)
    if 'semaine' not in nat.columns:
        if 'week_start' in nat.columns:
            nat['semaine'] = nat['week_start'].dt.date.astype(str) + '/' + (nat['week_start'] + pd.Timedelta(days=6)).dt.date.astype(str)
        else:
            nat['semaine'] = 'Unknown'

    # Normalise sex column name to 'sexe' for grouping
    if 'sexe' not in nat.columns:
        if 'sex' in nat.columns:
            nat['sexe'] = nat['sex']
        else:
            nat['sexe'] = 'Unknown'

    defaults = {
        'pcr_any_positif': pd.NA,
        'ct_value_num': pd.NA,
        'nb_symptomes': pd.NA,
        'severe': pd.NA,
        'charge_virale_cat': pd.NA,
    }
    nat = _ensure_columns(nat, defaults)

    group_cols = ['semaine', 'sexe', 'age_bin']
    grouped = nat.groupby(group_cols, dropna=False)

    agg = grouped.agg(
        total_cases=pd.NamedAgg(column='pcr_any_positif', aggfunc='size'),
        positivity_rate=pd.NamedAgg(column='pcr_any_positif', aggfunc=lambda s: s.astype(float).mean() if s.size>0 else np.nan),
        median_ct=pd.NamedAgg(column='ct_value_num', aggfunc=lambda s: s.dropna().median() if s.size>0 else np.nan),
        mean_nb_symptomes=pd.NamedAgg(column='nb_symptomes', aggfunc=lambda s: s.astype(float).mean() if s.size>0 else np.nan),
        proportion_severe=pd.NamedAgg(column='severe', aggfunc=lambda s: s.astype(float).mean() if s.size>0 else np.nan),
    ).reset_index()

    # charge_virale distribution counts per group
    if 'charge_virale_cat' in nat.columns:
        pivot = (
            nat.groupby(group_cols + ['charge_virale_cat'])
            .size()
            .unstack(fill_value=0)
            .rename_axis(columns=None)
            .reset_index()
        )
        pivot = pivot.rename(columns=lambda c: f'charge_virale_{c}' if c not in group_cols else c)
        national = pd.merge(agg, pivot, on=group_cols, how='left')
        dist_cols = [c for c in national.columns if c.startswith('charge_virale_')]
        if dist_cols:
            national[dist_cols] = national[dist_cols].fillna(0).astype(int)
    else:
        national = agg

    path = NATIONAL_OUTPUT_DIR / 'data_national.csv'
    # Attempt to merge forecast columns (week-level forecasts) if available
    try:
        fpath = FORECAST_OUTPUT_DIR / 'national_forecast.csv'
        if fpath.exists():
            fc = pd.read_csv(fpath)
            # ensure same 'semaine' formatting
            if 'semaine' not in fc.columns and 'ds' in fc.columns:
                fc['ds'] = pd.to_datetime(fc['ds'])
                fc['semaine'] = fc['ds'].dt.date.astype(str) + '/' + (fc['ds'] + pd.Timedelta(days=6)).dt.date.astype(str)
            # select relevant forecast columns
            keep = [c for c in ['semaine','forecast_incidence','inc_low','inc_high','forecast_positivity','pos_low','pos_high'] if c in fc.columns]
            if keep:
                fc2 = fc[keep].drop_duplicates(subset=['semaine'])
                national = national.merge(fc2, on='semaine', how='left')
                # compute ecart_% for positivity when both present
                if 'forecast_positivity' in national.columns and 'positivity_rate' in national.columns:
                    def pct_ecart(obs, pred):
                        try:
                            if np.isnan(pred) or pred == 0: return np.nan
                            return (float(obs) - float(pred)) / float(pred) * 100
                        except Exception:
                            return np.nan
                    national['ecart_%_positivity'] = national.apply(lambda r: pct_ecart(r['positivity_rate'], r.get('forecast_positivity', np.nan)), axis=1)
    except Exception as _e:
        print('Warning: could not merge national forecasts into data_national.csv:', _e)

    national.to_csv(path, index=False)
    return national


def build_international_dataset(df):
    """LEVEL 3 â€” INTERNATIONAL PARTNERS (WHO/ECDC)
    - Harmonized minimal dataset aggregated by week, age_group and sex
    - Age groups fixed to: 0-4,5-17,18-29,30-44,45-59,60+
    """
    intl = df.copy()

    # week
    if 'semaine' in intl.columns:
        intl['week'] = intl['semaine']
    elif 'pcr_lesionnaire_date_dt' in intl.columns:
        intl['week'] = intl['pcr_lesionnaire_date_dt'].dt.to_period('W').astype(str)
    else:
        intl['week'] = 'Unknown'

    # sex column
    if 'sexe' not in intl.columns:
        if 'sex' in intl.columns:
            intl['sexe'] = intl['sex']
        else:
            intl['sexe'] = 'Unknown'

    # age -> age_group
    if 'age' in intl.columns:
        intl['_age_num'] = pd.to_numeric(intl['age'], errors='coerce')
        bins = [0,5,18,30,45,60,200]
        labels = ['0-4','5-17','18-29','30-44','45-59','60+']
        intl['age_group'] = pd.cut(intl['_age_num'], bins=bins, labels=labels, right=False)
        intl['age_group'] = intl['age_group'].cat.add_categories(['Unknown']).fillna('Unknown')
        intl = intl.drop(columns=['_age_num'])
    elif 'age_bin' in intl.columns:
        intl['age_group'] = intl['age_bin'].astype(str).fillna('Unknown')
    else:
        intl['age_group'] = 'Unknown'

    # ensure metric cols
    defaults = {'pcr_any_positif': pd.NA, 'ct_value_num': pd.NA, 'severe': pd.NA}
    intl = _ensure_columns(intl, defaults)

    # travel flag
    travel_cols = [c for c in ['antecedent_voyage', 'voyage_zone_epidemie', 'voyage_zone', 'zone_epidemie'] if c in intl.columns]
    if travel_cols:
        tf = pd.Series(False, index=intl.index)
        for c in travel_cols:
            tf = tf | intl[c].fillna(False).astype(bool)
        intl['travel_related'] = tf
    else:
        intl['travel_related'] = False

    group_cols = ['week', 'age_group', 'sexe']
    grouped = intl.groupby(group_cols, dropna=False)
    international = grouped.agg(
        total_cases=pd.NamedAgg(column='pcr_any_positif', aggfunc='size'),
        positivity_rate=pd.NamedAgg(column='pcr_any_positif', aggfunc=lambda s: s.astype(float).mean() if s.size>0 else np.nan),
        severe_rate=pd.NamedAgg(column='severe', aggfunc=lambda s: s.astype(float).mean() if s.size>0 else np.nan),
        travel_related_rate=pd.NamedAgg(column='travel_related', aggfunc=lambda s: s.astype(float).mean() if s.size>0 else np.nan),
        median_ct=pd.NamedAgg(column='ct_value_num', aggfunc=lambda s: s.dropna().median() if s.size>0 else np.nan),
    ).reset_index()

    path = INTERNATIONAL_OUTPUT_DIR / 'data_international.csv'
    international.to_csv(path, index=False)
    return international


# Execute builders (non-destructive; robust to missing `df`)
try:
    _ = build_local_dataset(df)
    _ = build_national_dataset(df)
    _ = build_international_dataset(df)
except Exception as _e:
    print('Warning: could not build one or more dashboard datasets:', _e)

# HTML index (amÃ©liorÃ©: tri par numÃ©ro, sections thÃ©matiques)
outdir = STATIC_DASHBOARD_DIR
with open(outdir / 'dashboard.html', 'w', encoding='utf-8') as f:
    f.write('<html><head><meta charset="utf-8"><title>Dashboard MPXV - SynthÃ©tique</title><style>body{font-family:Arial;margin:20px;}img{max-width:100%;border:1px solid #ddd;margin:10px 0;}</style></head><body>')
    f.write('<h1>Dashboard MPXV - DonnÃ©es synthÃ©tiques</h1>')
    f.write('<h2>Surveillance et Diagnostic</h2>')
    for name in sorted(outdir.glob('0[1-2]*.png')): f.write(f'<h3>{name.name}</h3><img src="{name.name}">')
    f.write('<h2>InfectiositÃ© et Transmission</h2>')
    for name in sorted(outdir.glob('0[3,9]*.png')) + sorted(outdir.glob('1[0,3]*.png')): f.write(f'<h3>{name.name}</h3><img src="{name.name}">')
    f.write('<h2>Identification et Risques</h2>')
    for name in sorted(outdir.glob('0[4-5,8]*.png')) + sorted(outdir.glob('12*.png')): f.write(f'<h3>{name.name}</h3><img src="{name.name}">')
    f.write('<h2>PrÃ©vention et DÃ©mographie</h2>')
    for name in sorted(outdir.glob('0[6-7]*.png')) + sorted(outdir.glob('1[1,4]*.png')): f.write(f'<h3>{name.name}</h3><img src="{name.name}">')
    f.write('</body></html>')

print(f"\n[OK] Dashboard HTML cree: {outdir / 'dashboard.html'}")
print(f"Total graphiques generes: {len(list(outdir.glob('*.png')))}")


def _write_dashboard_html(path, title, sections):
    """Write a simple HTML file with given sections.
    sections: list of tuples (section_title, [filename,...])
    Filenames are expected to be relative to `path.parent`.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(f"<html><head><meta charset=\"utf-8\"><title>{title}</title>")
        f.write("<style>body{font-family:Arial;margin:20px;}img{max-width:100%;border:1px solid #ddd;margin:10px 0;} h1,h2{color:#222}</style>")
        f.write("</head><body>")
        f.write(f"<h1>{title}</h1>")
        for sec_title, files in sections:
            f.write(f"<h2>{sec_title}</h2>")
            any_shown = False
            for fn in files:
                p = outdir / fn
                if p.exists():
                    any_shown = True
                    f.write(f"<h3>{fn}</h3>")
                    f.write(f"<img src=\"{fn}\" alt=\"{fn}\">")
            if not any_shown:
                f.write('<p><em>Aucun graphique disponible pour cette section.</em></p>')
        f.write('</body></html>')


def build_local_dashboard(outdir):
    """Build `dashboard_local.html` for operational/local use.
    Includes case-level and operational graphs (if present).
    """
    sections = [
        ("Surveillance: incidence & positivitÃ©", [
            '01_surveillance_incidence_positivite_semaine.png'
        ]),
        ("Diagnostic: positivitÃ© par type d'Ã©chantillon", [
            '02_diagnostic_positivite_par_type.png'
        ]),
        ("Identification: symptÃ´mes et charge clinique", [
            '04_identification_nb_symptomes_par_statut.png',
        ]),
        ("MobilitÃ© / Exposition", [
            '10_transmission_positivite_par_mobilite.png'
        ]),
        ("InfectiositÃ©: Ct vs dÃ©lai", [
            '03a_infectiosite_ct_vs_delai_scatter.png',
            '03b_infectiosite_ct_vs_delai_box.png'
        ]),
        ("Ã‰tendue et localisation des lÃ©sions", [
            '09_infectiosite_nb_localisations_lesions.png',
            '13_transmission_nb_localisations_par_charge_virale.png'
        ]),
    ]
    # include forecast visuals when present
    sections[0][1].extend(['15_forecast_incidence.png','15_forecast_positivity.png'])
    _write_dashboard_html(outdir / 'dashboard_local.html', 'Dashboard MPXV â€” Local (OpÃ©rationnel)', sections)


def build_national_dashboard(outdir):
    """Build `dashboard_national.html` for national decision makers.
    Focuses on aggregated epidemiologic indicators and policy-relevant plots.
    """
    sections = [
        ("Tendances et positivitÃ©", [
            '01_surveillance_incidence_positivite_semaine.png'
        ]),
        ("SÃ©vÃ©ritÃ© et vulnÃ©rabilitÃ©s", [
            '05_risques_severite_par_vih.png',
            '12_vulnerabilites_severite_par_age.png'
        ]),
        ("PositivitÃ© par tranche d'Ã¢ge", [
            '11_ciblage_positivite_par_age.png'
        ]),
        ("Impact vaccinal et prÃ©vention", [
            '06_prevention_positivite_par_vaccin.png'
        ]),
        ("DÃ©mographie: distribution par Ã¢ge", [
            '07_demographie_age_par_statut.png'
        ]),
    ]
    # include forecast visuals when present
    sections[0][1].append('15_forecast_positivity.png')
    sections[0][1].append('15_forecast_incidence.png')
    _write_dashboard_html(outdir / 'dashboard_national.html', 'Dashboard MPXV â€” National (Situation Ã©pidÃ©miologique)', sections)


def build_international_dashboard(outdir):
    """Build `dashboard_international.html` for WHO/ECDC partners.
    Contains high-level harmonized indicators only.
    """
    sections = [
        ("Incidence & positivitÃ© (agrÃ©gÃ©s)", [
            '01_surveillance_incidence_positivite_semaine.png'
        ]),
        ("PositivitÃ© et sÃ©vÃ©ritÃ© (proportions)", [
            '11_ciblage_positivite_par_age.png',
            '12_vulnerabilites_severite_par_age.png'
        ]),
        ("RÃ©partition d'Ã¢ge des cas confirmÃ©s", [
            '07_demographie_age_par_statut.png'
        ]),
        ("Voyages / exposition (indicateur agrÃ©gÃ©)", [
            '10_transmission_positivite_par_mobilite.png'
        ]),
    ]
    # include forecast visuals when present
    sections[0][1].extend(['15_forecast_incidence.png','15_forecast_positivity.png'])
    _write_dashboard_html(outdir / 'dashboard_international.html', 'Dashboard MPXV â€” International (WHO / ECDC)', sections)


# Build the three separate dashboards (non-destructive; will skip missing PNGs)
try:
    build_local_dashboard(outdir)
    build_national_dashboard(outdir)
    build_international_dashboard(outdir)
    print('[OK] Dashboards crÃ©Ã©s: dashboard_local.html, dashboard_national.html, dashboard_international.html')
except Exception as e:
    print('Warning: error while creating dashboards:', e)

