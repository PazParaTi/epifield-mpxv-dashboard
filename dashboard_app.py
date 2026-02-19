import streamlit as st
import pandas as pd
import numpy as np
import base64
import re
import html
import streamlit.components.v1 as components
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(layout='wide', page_title='MPXV Dashboard (Interactive)')

# Global dark theme CSS: force white text and black background for app
_THEME_CSS = """
<style>
html, body, .stApp, .css-1d391kg, .block-container, .stSidebar, .sidebar .sidebar-content { background-color: #000 !important; color: #fff !important; }
* { color: #fff !important; }
a { color: #9ad0ff !important; }
.stButton>button { color: #000 !important; background-color: #fff !important; }
.dataframe td, .dataframe th { color: #fff !important; }
.st-c { color: #fff !important; }
</style>
"""
st.markdown(_THEME_CSS, unsafe_allow_html=True)

# --- Helpers ---
# Resolve dashboard outputs directory: prefer app-local `dashboard_outputs`,
# otherwise fall back to `Script extraction/dashboard_outputs` used by `analyse.py`.
BASE_DIR = Path(__file__).parent
_candidates = [BASE_DIR / 'dashboard_outputs', BASE_DIR / 'Script extraction' / 'dashboard_outputs', Path('dashboard_outputs')]
DATA_DIR = None
for _p in _candidates:
    if _p.exists():
        DATA_DIR = _p
        break
if DATA_DIR is None:
    DATA_DIR = BASE_DIR / 'dashboard_outputs'  # default path (may be empty)

# Use file modification times to bust cache when CSVs change
def _file_mtimes():
    files = ['data_national.csv', 'national_forecast.csv', 'data_local.csv', 'data_international.csv']
    mt = []
    for fn in files:
        p = DATA_DIR / fn
        try:
            mt.append(p.stat().st_mtime)
        except Exception:
            mt.append(0)
    return tuple(mt)


@st.cache_data
def load_data_with_mtimes(mtimes):
    # Load national + forecast + local + international if present
    nat = pd.read_csv(DATA_DIR / 'data_national.csv') if (DATA_DIR / 'data_national.csv').exists() else pd.DataFrame()
    fc = pd.read_csv(DATA_DIR / 'national_forecast.csv') if (DATA_DIR / 'national_forecast.csv').exists() else pd.DataFrame()
    local_df = pd.read_csv(DATA_DIR / 'data_local.csv') if (DATA_DIR / 'data_local.csv').exists() else pd.DataFrame()
    intl_df = pd.read_csv(DATA_DIR / 'data_international.csv') if (DATA_DIR / 'data_international.csv').exists() else pd.DataFrame()

    # Basic preparation for local_df (case-level)
    try:
        if not local_df.empty:
            # coerce date columns
            for c in ['semaine','date_premiers_symptomes','pcr_lesionnaire_date']:
                if c in local_df.columns:
                    local_df[c] = pd.to_datetime(local_df[c], errors='coerce')
            # booleans: common names
            for bcol in ['pcr_any_positif','severe','pcr_lesion_positif','pcr_oropharynx_positif']:
                if bcol in local_df.columns:
                    local_df[bcol] = local_df[bcol].astype(bool)
            # numeric ct/delay
            for ncol in ['ct_value_num','delai_symptomes_vers_pcr_jours','age','total_cases']:
                if ncol in local_df.columns:
                    local_df[ncol] = pd.to_numeric(local_df[ncol], errors='coerce')
    except Exception:
        pass

    # Basic preparation for intl_df (aggregates)
    try:
        if not intl_df.empty:
            if 'semaine' in intl_df.columns:
                intl_df['ds'] = pd.to_datetime(intl_df['semaine'].str.split('/').str[0], errors='coerce')
            for ncol in ['positivity_rate','severe_rate','forecast_positivity','forecast_incidence']:
                if ncol in intl_df.columns:
                    intl_df[ncol] = pd.to_numeric(intl_df[ncol], errors='coerce')
    except Exception:
        pass

    return nat, fc, local_df, intl_df


nat, fc, local_df, intl_df = load_data_with_mtimes(_file_mtimes())

# NOTE: CSV previews moved to bottom of the sidebar inside an expander
# to avoid cluttering the top of the sidebar (filters remain prominent).

# Show which data directory is used and availability
st.sidebar.markdown(f"**Dossier de données utilisé:** {DATA_DIR}")
files_check = {
    'data_national.csv': (DATA_DIR / 'data_national.csv').exists(),
    'national_forecast.csv': (DATA_DIR / 'national_forecast.csv').exists(),
    'data_local.csv': (DATA_DIR / 'data_local.csv').exists(),
    'data_international.csv': (DATA_DIR / 'data_international.csv').exists(),
}
st.sidebar.write('Fichiers disponibles:')
for fn, ok in files_check.items():
    st.sidebar.write(f"- {fn}: {'OK' if ok else 'MANQUANT'}")

# move CSV previews to a collapsible expander at the BOTTOM of the sidebar
# (we will render the expander after filters are declared below)

def alert_level(p):
    try:
        p = float(p)
    except Exception:
        return ('NA', 'gray', '', 'N/A')
    if p > 0.5:
        return ('Critique', '#000000', '🚨', 'Critique')
    if p > 0.3:
        return ('Danger', '#d62728', '🛑', 'Danger')
    if p > 0.15:
        return ('Vigilance', '#ff7f0e', '⚠️', 'Vigilance')
    return ('RAS', '#2ca02c', '✅', 'RAS')


def render_kpi(col, title, value, subtitle, color, emoji):
    html = f"""
    <div style='padding:12px;border-radius:8px;background:{color};color:white;'>
      <div style='font-size:14px;opacity:0.9'>{title}</div>
      <div style='font-size:22px;font-weight:700;margin-top:6px'>{emoji} {value}</div>
      <div style='font-size:12px;opacity:0.9;margin-top:6px'>{subtitle}</div>
    </div>
    """
    col.markdown(html, unsafe_allow_html=True)


def commentary_from_ecart(ecart_pct, level_label):
    try:
        if pd.isna(ecart_pct):
            return ''
        pct = float(ecart_pct)
    except Exception:
        return ''
    sign = '+' if pct >= 0 else ''
    if level_label == 'Critique':
        tone = 'Augmentation critique — action immédiate recommandée.'
    elif level_label == 'Danger':
        tone = 'Augmentation importante — enquêter sur clusters.'
    elif level_label == 'Vigilance':
        tone = 'Légère hausse — surveiller l’évolution.'
    else:
        tone = 'Rien d’inquiétant.'
    return f"Écart {sign}{round(pct,1)}% : {level_label} — {tone}"

# Sidebar
st.sidebar.title('Filtres')
locale = st.sidebar.selectbox('Niveau', ['National', 'Local', 'International'])
lang = st.sidebar.selectbox('Langue / Language', ['Français','English'])
# date range filter if possible
min_ds = None
max_ds = None
if not nat.empty:
    try:
        nat['ds'] = pd.to_datetime(nat['semaine'].str.split('/').str[0])
        min_ds = nat['ds'].min(); max_ds = nat['ds'].max()
    except Exception:
        pass
if min_ds is not None and max_ds is not None:
    dr = st.sidebar.date_input('Période', [min_ds.date(), max_ds.date()])
else:
    dr = None

age_choices = sorted(nat['age_bin'].dropna().unique()) if 'age_bin' in nat.columns else []
age_sel = st.sidebar.multiselect('Age bins', options=age_choices, default=age_choices)
show_severe = st.sidebar.checkbox('Afficher seulement cas sévères', value=False)
# Region and season filters
region_choices = sorted(nat['region'].dropna().unique()) if 'region' in nat.columns else []
region_sel = st.sidebar.multiselect('Régions', options=region_choices, default=region_choices)
season_min, season_max = st.sidebar.slider('Niveau saison pluvieuse (min,max)', 0.0, 1.0, (0.0, 1.0), step=0.05)

# CSV previews placed at bottom of sidebar inside an expander to avoid clutter
with st.sidebar.expander('Previews CSV (debug)', expanded=False):
    try:
        st.write('Preview: data_national.csv rows,cols =', (nat.shape if not nat.empty else (0,0)))
        if not nat.empty:
            st.write(nat.head(3))
        st.write('Preview: national_forecast.csv rows,cols =', (fc.shape if not fc.empty else (0,0)))
        if not fc.empty:
            st.write(fc.head(3))
        st.write('Preview: data_local.csv rows,cols =', (local_df.shape if not local_df.empty else (0,0)))
        if not local_df.empty:
            st.write(local_df.head(3))
        st.write('Preview: data_international.csv rows,cols =', (intl_df.shape if not intl_df.empty else (0,0)))
        if not intl_df.empty:
            st.write(intl_df.head(3))
    except Exception:
        pass

# Small debug: warn if national data is missing
if nat.empty:
    st.sidebar.warning('Données nationales vides — exécutez analyse.py pour générer les CSV')

# Top KPIs (styled)
st.title('MPXV Dashboard - Interactive (Prototype)')

# show last update from data_national.csv mtime when available
nat_file = DATA_DIR / 'data_national.csv'
try:
    if nat_file.exists():
        last_update = pd.to_datetime(nat_file.stat().st_mtime, unit='s')
    else:
        last_update = pd.Timestamp.now()
except Exception:
    last_update = pd.Timestamp.now()
st.write('Dernière mise à jour des CSV: ', last_update.strftime('%Y-%m-%d %H:%M'))

# -----------------------
# Global KPIs (5 cards)
# -----------------------
# We'll try to compute metrics from `nat` first, falling back to `local_df`.
def _safe_to_datetime_ser(df, colname):
    try:
        if colname in df.columns:
            return pd.to_datetime(df[colname], errors='coerce')
    except Exception:
        pass
    return pd.Series(pd.NaT, index=df.index)

def _get_latest_row(df):
    if df.empty:
        return None
    # prefer 'ds' then 'semaine' for week start
    if 'ds' in df.columns:
        try:
            df2 = df.copy()
            df2['ds'] = pd.to_datetime(df2['ds'], errors='coerce')
            if df2['ds'].notna().any():
                return df2.sort_values('ds').iloc[-1]
        except Exception:
            pass
    if 'semaine' in df.columns:
        try:
            df2 = df.copy()
            df2['ds'] = pd.to_datetime(df2['semaine'].str.split('/').str[0], errors='coerce')
            if df2['ds'].notna().any():
                return df2.sort_values('ds').iloc[-1]
        except Exception:
            pass
    return df.iloc[-1]

def _get_cases_from_row(row):
    for k in ('n','total_cases','cases','count'):
        if k in row.index:
            try:
                return int(row.get(k, 0) or 0)
            except Exception:
                continue
    # fall back to 'pcr_any_positif' counts if row is from local case-level
    return None

def _get_positivity_from_row(row):
    for k in ('positivity_rate','positivite_%','positivite','positivity'):
        if k in row.index:
            try:
                v = row.get(k, None)
                if pd.isna(v):
                    return None
                return float(v)
            except Exception:
                continue
    return None

def _compute_global_kpis():
    # default values
    out = dict(incidence='N/A', tests_per_case='N/A', positivity_last='N/A', positivity_global='N/A', alert_label='N/A', alert_color='#6c757d', alert_emoji='')
    # prefer aggregated national data
    source = nat if (not nat.empty) else local_df
    if source is None or source.empty:
        return out

    # latest row
    latest = _get_latest_row(source)

    # incidence (cases last week)
    inc = None
    if latest is not None:
        inc = _get_cases_from_row(latest)
    if inc is None:
        # try aggregate count from source
        if 'total_cases' in source.columns:
            try:
                inc = int(source['total_cases'].dropna().astype(int).iloc[-1])
            except Exception:
                inc = None
    if inc is None and not local_df.empty:
        # compute from local_df by grouping on semaine
        try:
            grp = local_df.groupby('semaine').size()
            if not grp.empty:
                inc = int(grp.iloc[-1])
        except Exception:
            inc = None

    out['incidence'] = f"{inc} cas" if inc is not None else 'N/A'

    # positivity last week
    pos_val = None
    if latest is not None:
        pos_val = _get_positivity_from_row(latest)
    if pos_val is None and not local_df.empty and 'pcr_any_positif' in local_df.columns:
        try:
            # compute positivity in most recent week in local
            ld = local_df.copy()
            if 'semaine' in ld.columns:
                lastw = ld['semaine'].dropna().unique()[-1]
                sub = ld[ld['semaine']==lastw]
                pos_val = float(sub['pcr_any_positif'].astype(int).sum()/len(sub)) if len(sub)>0 else None
        except Exception:
            pos_val = None

    out['positivity_last'] = (f"{round(pos_val*100,1)}%" if (pos_val is not None and not pd.isna(pos_val)) else 'N/A')

    # global positivity (mean or weighted if n present)
    try:
        if (not nat.empty) and ('positivity_rate' in nat.columns):
            if 'n' in nat.columns:
                w = pd.to_numeric(nat['n'], errors='coerce').fillna(0)
                pr = pd.to_numeric(nat['positivity_rate'], errors='coerce').fillna(np.nan)
                if w.sum()>0:
                    weighted = (pr.fillna(0)*w).sum() / w.sum()
                    out['positivity_global'] = f"{round(weighted*100,1)}%"
                else:
                    out['positivity_global'] = f"{round(pr.mean()*100,1)}%"
            else:
                out['positivity_global'] = f"{round(nat['positivity_rate'].dropna().mean()*100,1)}%"
        elif not local_df.empty and 'pcr_any_positif' in local_df.columns:
            p = local_df['pcr_any_positif'].astype(int).sum()/len(local_df) if len(local_df)>0 else np.nan
            out['positivity_global'] = (f"{round(p*100,1)}%" if not pd.isna(p) else 'N/A')
    except Exception:
        out['positivity_global'] = out['positivity_last']

    # tests per case: prefer local_df tests/cases when available
    tpc = 'N/A'
    try:
        if not local_df.empty and 'pcr_any_positif' in local_df.columns:
            tests = len(local_df)
            cases = int(local_df['pcr_any_positif'].astype(int).sum()) if 'pcr_any_positif' in local_df.columns else 0
            if cases>0:
                tpc = f"{round(tests/cases,1)}"
        elif pos_val is not None and pos_val>0:
            # approximate tests/case = 1/positivity
            tpc = f"{round(1.0/pos_val,1)}"
    except Exception:
        tpc = 'N/A'
    out['tests_per_case'] = tpc

    # alert level based on last positivity value
    try:
        lvl, colr, emj, _ = alert_level(pos_val if pos_val is not None else np.nan)
        out['alert_label'] = lvl
        out['alert_color'] = colr
        out['alert_emoji'] = emj
    except Exception:
        out['alert_label'] = 'N/A'; out['alert_color'] = '#6c757d'; out['alert_emoji'] = ''

    return out

KPIs = _compute_global_kpis()

# render five KPI cards across the page
cols = st.columns(5)
render_kpi(cols[0], 'Incidence (dernière semaine)', KPIs['incidence'], 'Cas (semaine la plus récente)', '#333333' if KPIs['incidence']!='N/A' else '#6c757d', '📈')
render_kpi(cols[1], 'Tests / cas', KPIs['tests_per_case'], 'Moyenne tests par cas', '#333333' if KPIs['tests_per_case']!='N/A' else '#6c757d', '🧾')
render_kpi(cols[2], 'Positivité (dernière semaine)', KPIs['positivity_last'], 'Taux de positivité', KPIs['alert_color'], KPIs['alert_emoji'])
render_kpi(cols[3], 'Taux de positivité (global)', KPIs['positivity_global'], 'Moyenne globale', KPIs['alert_color'], '')
render_kpi(cols[4], 'Alerte', KPIs['alert_label'], '', KPIs['alert_color'], KPIs['alert_emoji'])

st.markdown('---')

# Main plot: incidence with forecast
tabs = st.tabs(['National','Local','International','Dashboards statiques'])

with tabs[0]:
    st.header('National: Incidence par semaine (historique + prévision)')
    if not nat.empty:
        # apply filters
        dfn = nat.copy()
        if dr is not None:
            start, end = pd.to_datetime(dr[0]), pd.to_datetime(dr[1])
            dfn['ds'] = pd.to_datetime(dfn['semaine'].str.split('/').str[0], errors='coerce')
            dfn = dfn[(dfn['ds']>=start) & (dfn['ds']<=end)]
        if age_sel:
            if 'age_bin' in dfn.columns:
                dfn = dfn[dfn['age_bin'].isin(age_sel)]
        if region_sel and 'region' in dfn.columns:
            dfn = dfn[dfn['region'].isin(region_sel)]
        # season filter
        if 'saison_pluvieuse_level' in dfn.columns:
            dfn = dfn[(dfn['saison_pluvieuse_level'] >= float(season_min)) & (dfn['saison_pluvieuse_level'] <= float(season_max))]
        if show_severe and 'severe' in dfn.columns:
            dfn = dfn[dfn['severe']==True]

        ts = dfn.groupby('semaine').agg(total_cases=('total_cases','sum'), positivity_rate=('positivity_rate','mean')).reset_index()

        # parse week start to ds if possible
        try:
            ts['ds'] = pd.to_datetime(ts['semaine'].str.split('/').str[0])
        except Exception:
            ts['ds'] = pd.date_range(end=pd.Timestamp.today(), periods=len(ts), freq='W')

        fig = go.Figure()
        fig.add_trace(go.Bar(x=ts['ds'], y=ts['total_cases'], name='Testés / cas (historique)', marker_color='#9ecae1'))
        if not fc.empty and 'ds' in fc.columns:
            fc2 = fc.copy()
            fc2['ds'] = pd.to_datetime(fc2['ds'])
            fig.add_trace(go.Scatter(x=fc2['ds'], y=fc2['forecast_incidence'], mode='lines', name='Prévision', line=dict(dash='dash', color='green')))
            if 'inc_low' in fc2.columns and 'inc_high' in fc2.columns:
                fig.add_trace(go.Scatter(x=fc2['ds'], y=fc2['inc_high'], mode='lines', name='CI sup', line=dict(width=0), showlegend=False))
                fig.add_trace(go.Scatter(x=fc2['ds'], y=fc2['inc_low'], mode='lines', name='CI inf', fill='tonexty', fillcolor='rgba(0,200,0,0.1)', line=dict(width=0), showlegend=False))
        fig.update_layout(xaxis_title='Semaine', yaxis_title='Cas')
        st.plotly_chart(fig, use_container_width=True)

        # Monthly incidence with season overlay (interactive)
        try:
            dfn['ds'] = pd.to_datetime(dfn['semaine'].str.split('/').str[0], errors='coerce')
            monthly = dfn.groupby(pd.Grouper(key='ds', freq='M')).agg(total_cases=('total_cases','sum'), positivity_rate=('positivity_rate','mean')).reset_index()
            monthly['saison_level'] = monthly['ds'].dt.month.apply(lambda m: 0.5*(1+np.sin(-2*np.pi*((m-8)/12.0))))
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(x=monthly['ds'], y=monthly['total_cases'], name='Cas (mensuel)', marker_color='#9ecae1'))
            fig2.add_trace(go.Scatter(x=monthly['ds'], y=monthly['saison_level']*monthly['total_cases'].max(), mode='lines+markers', name='Saison (scaled)', line=dict(color='red', dash='dash')))
            fig2.update_layout(title='Incidence mensuelle et niveau saisonnier', xaxis_title='Mois', yaxis_title='Cas (mensuel)')
            st.plotly_chart(fig2, use_container_width=True)
        except Exception:
            pass

        # Interactive heatmap: regional positivity monthly if CSV exists
        heat_csv = DATA_DIR / 'regional_positivity_monthly.csv'
        if heat_csv.exists():
            try:
                hv = pd.read_csv(heat_csv)
                # pivot expects columns: region + months as columns
                pivot = hv.set_index('region')
                months = [c for c in pivot.columns if c != 'region'] if 'region' in pivot.columns else list(pivot.columns)
                # If months are datetime-like strings, try to convert
                pivot2 = pivot.copy()
                pivot2.columns = [str(c) for c in pivot2.columns]
                fig3 = go.Figure(data=go.Heatmap(z=pivot2.values, x=pivot2.columns, y=pivot2.index, colorscale='OrRd'))
                fig3.update_layout(title='Heatmap: positivité par région et mois', xaxis_title='Mois', yaxis_title='Région')
                st.plotly_chart(fig3, use_container_width=True)
            except Exception as _e:
                st.sidebar.error(f'Erreur heatmap: {_e}')

        # Auto commentary below chart based on last ecart vs forecast
        try:
            if 'ecart_%_positivity' in dfn.columns:
                last_row = dfn.sort_values('ds').iloc[-1]
                ec = last_row.get('ecart_%_positivity', None)
            else:
                # try to pull from global fc merge
                ec = dfn.get('ecart_%_positivity', pd.NA).dropna().iloc[-1] if 'ecart_%_positivity' in dfn.columns else None
        except Exception:
            ec = None
        try:
            latest_for_level = _get_latest_row(dfn) if (dfn is not None and not dfn.empty) else None
            pos_for_level = _get_positivity_from_row(latest_for_level) if latest_for_level is not None else None
            level = alert_level(pos_for_level if (pos_for_level is not None and not pd.isna(pos_for_level)) else np.nan)[0]
        except Exception:
            level = 'RAS'
        comment = commentary_from_ecart(ec, level)
        if comment:
            st.markdown(f"**Commentaire:** {comment}")
    else:
        st.info('Aucune donnée nationale disponible. Exécutez `analyse.py` pour générer les CSV.')

with tabs[1]:
    st.header('Local: indicateurs et cas récents')
    # prefer cached local_df, otherwise read from file
    try:
        if local_df is None or local_df.empty:
            local_path = DATA_DIR / 'data_local.csv'
            has_local = local_path.exists()
            df_local = pd.read_csv(local_path) if has_local else pd.DataFrame()
        else:
            df_local = local_df.copy()
    except Exception as _e:
        st.sidebar.error(f"Erreur d'accès au fichier local: {repr(_e)}")
        df_local = pd.DataFrame()

    if df_local.empty:
        st.info('Aucun fichier local trouvé ou vide. Exécutez `analyse.py`.')
    else:
        # local filters
        local_regions = sorted(df_local['region'].dropna().unique()) if 'region' in df_local.columns else []
        local_region_sel = st.sidebar.multiselect('Régions (Local)', options=local_regions, default=local_regions)
        if local_region_sel and 'region' in df_local.columns:
            df_local = df_local[df_local['region'].isin(local_region_sel)]
        if show_severe and 'severe' in df_local.columns:
            df_local = df_local[df_local['severe']==True]

        # KPIs
        try:
            total_cases = int(df_local['total_cases'].sum()) if 'total_cases' in df_local.columns else len(df_local)
            positivity = (df_local['positivity_rate'].mean() if 'positivity_rate' in df_local.columns else (df_local['pcr_any_positif'].mean() if 'pcr_any_positif' in df_local.columns else np.nan))
            severe_rate = (df_local['severe'].mean() if 'severe' in df_local.columns else np.nan)
            median_age = int(df_local['age'].median()) if 'age' in df_local.columns else 'N/A'
        except Exception:
            total_cases, positivity, severe_rate, median_age = 0, np.nan, np.nan, 'N/A'

        k1, k2, k3 = st.columns(3)
        lvl, color, emoji, _ = alert_level(positivity if not pd.isna(positivity) else np.nan)
        render_kpi(k1, 'Cas locaux (total)', f"{total_cases}", 'Nombre de cas recensés', '#333333' if total_cases>0 else '#6c757d', '🧾')
        render_kpi(k2, 'Positivité locale', f"{round(positivity*100,1) if not pd.isna(positivity) else 'N/A'}%", 'Taux moyen', color, emoji)
        render_kpi(k3, 'Cas sévères', f"{round(severe_rate*100,1) if not pd.isna(severe_rate) else 'N/A'}%", f'Âge médian: {median_age}', ('#d62728' if severe_rate and severe_rate>0.15 else '#2ca02c'), '🛑' if severe_rate and severe_rate>0.15 else '✅')

        st.markdown('---')

        # Age distribution by PCR status
        try:
            bins = [0,4,17,29,44,59,200]
            labels = ['0-4','5-17','18-29','30-44','45-59','60+']
            if 'age' in df_local.columns:
                df_local['age_bin'] = pd.cut(df_local['age'], bins=bins, labels=labels)
                grp = df_local.groupby(['age_bin', 'pcr_any_positif']).size().unstack(fill_value=0)
                fig_age = go.Figure()
                neg = grp.get(False, pd.Series(0, index=grp.index))
                pos = grp.get(True, pd.Series(0, index=grp.index))
                fig_age.add_trace(go.Bar(x=grp.index.astype(str), y=neg.values, name='PCR -', marker_color='#9ecae1'))
                fig_age.add_trace(go.Bar(x=grp.index.astype(str), y=pos.values, name='PCR +', marker_color='#de2d26'))
                fig_age.update_layout(barmode='stack', title='Distribution âge par statut PCR', xaxis_title='Tranche âge', yaxis_title='Nombre de cas', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_age, use_container_width=True)
        except Exception:
            pass

        # Positivity by mobility group
        try:
            if 'mobilite_groupe' in df_local.columns and 'pcr_any_positif' in df_local.columns:
                mg = df_local.groupby('mobilite_groupe').agg(n=('pcr_any_positif','size'), pos=('pcr_any_positif','sum')).reset_index()
                mg['p'] = mg['pos'] / mg['n']
                def _wilson(k,n,z=1.96):
                    if n==0: return 0,0,0
                    phat = k/n
                    denom = 1 + z*z/n
                    center = (phat + z*z/(2*n))/denom
                    half = (z*( (phat*(1-phat)/n + z*z/(4*n*n))**0.5))/denom
                    return center, max(0, center-half), min(1, center+half)
                errs = [(_wilson(int(r.pos), int(r.n))[0]-_wilson(int(r.pos), int(r.n))[1])*100 for _,r in mg.iterrows()]
                fig_mob = go.Figure()
                fig_mob.add_trace(go.Bar(x=mg['mobilite_groupe'], y=mg['p']*100, error_y=dict(type='data', array=errs), marker_color='#9ad0ff'))
                fig_mob.update_layout(title='Positivité par groupe mobilité', yaxis_title='Positivité (%)', xaxis_title='Groupe mobilité', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_mob, use_container_width=True)
        except Exception:
            pass

        # Ct vs délai scatter
        try:
            if 'ct_value_num' in df_local.columns and 'delai_symptomes_vers_pcr_jours' in df_local.columns:
                colors = df_local['severe'].map({True:'#de2d26', False:'#9ecae1'}) if 'severe' in df_local.columns else '#9ecae1'
                fig_ct = go.Figure()
                fig_ct.add_trace(go.Scatter(x=df_local['delai_symptomes_vers_pcr_jours'], y=df_local['ct_value_num'], mode='markers', marker=dict(color=colors, size=8), text=df_local.get('region', None), hovertemplate='Delay: %{x}d<br>Ct: %{y}<extra></extra>'))
                fig_ct.update_layout(title='Ct vs délai (cas locaux)', xaxis_title='Délai symptômes→PCR (jours)', yaxis_title='Ct', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_ct, use_container_width=True)
        except Exception:
            pass

        st.markdown('---')
        # table at bottom
        try:
            st.data_editor(df_local.head(200), num_rows='dynamic')
        except Exception:
            st.dataframe(df_local.head(200))

with tabs[2]:
    st.header('International: indicateurs et tendances')
    try:
        if intl_df is None or intl_df.empty:
            intl_path = DATA_DIR / 'data_international.csv'
            has_intl = intl_path.exists()
            df_intl = pd.read_csv(intl_path) if has_intl else pd.DataFrame()
        else:
            df_intl = intl_df.copy()
    except Exception as _e:
        st.sidebar.error(f"Erreur d'accès au fichier international: {repr(_e)}")
        df_intl = pd.DataFrame()

    if df_intl.empty:
        st.info('Aucun fichier international trouvé ou vide. Exécutez `analyse.py`.')
    else:
        # filters
        include_forecast = st.sidebar.checkbox('Inclure prévisions (International)', value=True)
        date_min = df_intl['ds'].min() if 'ds' in df_intl.columns else None
        date_max = df_intl['ds'].max() if 'ds' in df_intl.columns else None
        if date_min is not None and date_max is not None:
            dr_int = st.sidebar.date_input('Période (Intl)', [date_min.date(), date_max.date()])
            start_i, end_i = pd.to_datetime(dr_int[0]), pd.to_datetime(dr_int[1])
            if 'ds' in df_intl.columns:
                df_intl = df_intl[(df_intl['ds']>=start_i) & (df_intl['ds']<=end_i)]

        # KPIs international
        try:
            pos_global = df_intl['positivity_rate'].mean() if 'positivity_rate' in df_intl.columns else np.nan
            sev_global = df_intl['severe_rate'].mean() if 'severe_rate' in df_intl.columns else np.nan
            travel_rate = df_intl['travel_related_rate'].mean() if 'travel_related_rate' in df_intl.columns else (df_intl.get('travel_related', pd.Series()).mean() if 'travel_related' in df_intl.columns else np.nan)
        except Exception:
            pos_global, sev_global, travel_rate = np.nan, np.nan, np.nan

        c1, c2, c3 = st.columns(3)
        l_label, l_color, l_emoji, _ = alert_level(pos_global if not pd.isna(pos_global) else np.nan)
        render_kpi(c1, 'Positivité globale', f"{round(pos_global*100,1) if not pd.isna(pos_global) else 'N/A'}%", 'Moyenne', l_color, l_emoji)
        render_kpi(c2, 'Taux sévère', f"{round(sev_global*100,1) if not pd.isna(sev_global) else 'N/A'}%", 'Sévérité moyenne', ('#d62728' if sev_global and sev_global>0.15 else '#2ca02c'), '🛑' if sev_global and sev_global>0.15 else '✅')
        render_kpi(c3, 'Cas liés voyages', f"{round(travel_rate*100,1) if not pd.isna(travel_rate) else 'N/A'}%", 'Proportion', '#333333', '🛫')

        st.markdown('---')

        # Incidence & positivity by week (with optional forecast)
        try:
            if 'ds' in df_intl.columns:
                fig_i = go.Figure()
                if 'incidence' in df_intl.columns:
                    fig_i.add_trace(go.Bar(x=df_intl['ds'], y=df_intl['incidence'], name='Incidence', marker_color='#9ecae1'))
                if 'positivity_rate' in df_intl.columns:
                    fig_i.add_trace(go.Scatter(x=df_intl['ds'], y=df_intl['positivity_rate']*100, mode='lines+markers', name='Positivité (%)', yaxis='y2', line=dict(color='#de2d26')))
                # forecast if requested
                if include_forecast and 'forecast_positivity' in df_intl.columns:
                    fig_i.add_trace(go.Scatter(x=df_intl['ds'], y=df_intl['forecast_positivity']*100, mode='lines', name='Prévision positivité', line=dict(dash='dash', color='orange')))
                fig_i.update_layout(title='Incidence & Positivité (International)', xaxis_title='Semaine', yaxis=dict(title='Incidence'), yaxis2=dict(title='Positivité (%)', overlaying='y', side='right'))
                st.plotly_chart(fig_i, use_container_width=True)
        except Exception:
            pass

        # Positivity by age group
        try:
            if 'age_group' in df_intl.columns or 'age_bin' in df_intl.columns or 'age' in df_intl.columns:
                if 'age_group' in df_intl.columns:
                    ag = df_intl.groupby('age_group').agg(p=('positivity_rate','mean')).reset_index()
                    x = ag['age_group']
                    y = ag['p']*100
                elif 'age_bin' in df_intl.columns:
                    ag = df_intl.groupby('age_bin').agg(p=('positivity_rate','mean')).reset_index()
                    x = ag['age_bin']
                    y = ag['p']*100
                else:
                    # bin ages
                    df_intl['age_bin'] = pd.cut(df_intl['age'], bins=[0,4,17,29,44,59,200], labels=['0-4','5-17','18-29','30-44','45-59','60+'])
                    ag = df_intl.groupby('age_bin').agg(p=('positivity_rate','mean')).reset_index()
                    x = ag['age_bin']; y = ag['p']*100
                fig_age_i = go.Figure(data=[go.Bar(x=x.astype(str), y=y, marker_color='#9ad0ff')])
                fig_age_i.update_layout(title='Positivité par groupe d\'âge (International)', yaxis_title='Positivité (%)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_age_i, use_container_width=True)
        except Exception:
            pass

        # Heatmap severity by region x week if available
        try:
            if 'region' in df_intl.columns and 'ds' in df_intl.columns and 'severe_rate' in df_intl.columns:
                piv = df_intl.pivot_table(index='region', columns='ds', values='severe_rate', aggfunc='mean').fillna(0)
                fig_h = go.Figure(data=go.Heatmap(z=piv.values, x=[str(x) for x in piv.columns], y=piv.index, colorscale='Viridis'))
                fig_h.update_layout(title='Heatmap: taux sévères par région et semaine', xaxis_title='Semaine', yaxis_title='Région')
                st.plotly_chart(fig_h, use_container_width=True)
        except Exception:
            pass

        st.markdown('---')
        try:
            st.dataframe(df_intl.head(200))
        except Exception:
            st.write(df_intl.head(200))

st.markdown('---')
st.caption('Prototype interactif — Phase 1: prévisions et KPIs.')

def _inline_images_in_html(html_text, base_path: Path):
    # find all src attributes in img tags
    def _replace(match):
        src = match.group(1)
        # ignore absolute URLs
        if src.startswith('http') or src.startswith('data:'):
            return f'src="{src}"'
        p = base_path / src
        if not p.exists():
            return f'src="{src}"'
        b = p.read_bytes()
        ext = p.suffix.lower().lstrip('.')
        mime = 'image/png' if ext in ['png'] else ('image/jpeg' if ext in ['jpg','jpeg'] else ('image/svg+xml' if ext=='svg' else 'application/octet-stream'))
        data = base64.b64encode(b).decode('ascii')
        return f'src="data:{mime};base64,{data}"'

    return re.sub(r'src=["\']([^"\']+)["\']', _replace, html_text)


with tabs[3]:
    st.header('Dashboards statiques générés')
    html_files = []
    for fn in ['dashboard_local.html','dashboard_national.html','dashboard_international.html','dashboard.html']:
        p = DATA_DIR / fn
        if p.exists():
            html_files.append((fn, p))
    if not html_files:
        st.info('Aucun fichier HTML statique trouvé dans le dossier de données.')
    else:
        choice = st.selectbox('Choisir un dashboard', [f[0] for f in html_files])
        sel_path = dict(html_files)[choice]
        try:
            raw = sel_path.read_text(encoding='utf-8')
            inlined = _inline_images_in_html(raw, sel_path.parent)
            components.html(_THEME_CSS + inlined, height=900, scrolling=True)
        except Exception as e:
            st.error(f"Impossible d'afficher le HTML: {e}")