import os
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def find_any(path_patterns):
    for p in path_patterns:
        if Path(p).exists():
            return Path(p)
    for p in REPO.rglob('donnees_synthetiques_flat.csv'):
        return p
    return None


def test_run_rdmstats():
    script = REPO / 'sources_donnees' / 'generateurs_synthetiques' / 'rdmStats.py'
    assert script.exists(), f"rdmStats.py not found at {script}"
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    result = subprocess.run([sys.executable, str(script)], cwd=str(REPO), capture_output=True, text=True, env=env)
    assert result.returncode == 0, f"rdmStats failed: {result.stdout}\n{result.stderr}"

    csv = find_any([REPO / 'donnees' / 'synthetiques' / 'exports_script_extraction' / 'donnees_synthetiques_flat.csv'])
    assert csv is not None and csv.exists(), 'Synthetic CSV not generated'


def test_run_analyse():
    script = REPO / 'traitement' / 'analyse_prevision' / 'analyse.py'
    assert script.exists(), f"analyse.py not found at {script}"
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    result = subprocess.run([sys.executable, str(script)], cwd=str(REPO), capture_output=True, text=True, env=env)
    assert result.returncode == 0, f"analyse failed: {result.stdout}\n{result.stderr}"

    out = REPO / 'sorties_intermediaires' / 'previsions' / 'national_forecast.csv'
    assert out.exists(), 'national_forecast.csv not found in expected outputs'
