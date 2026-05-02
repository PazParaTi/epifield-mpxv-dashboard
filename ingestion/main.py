from pathlib import Path

from extract_word import load_all_word_files
from aggregator import aggregate_all_docs
from export import save_to_csv, save_to_json


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CRF_DIR = PROJECT_ROOT / "sources_donnees" / "crf_word"
OUTPUT_DIR = PROJECT_ROOT / "donnees" / "reelles"


print("Chargement des fichiers Word...")
docs = load_all_word_files(CRF_DIR)

print("Extraction des donnees...")
rows = aggregate_all_docs(docs)

print("Export CSV/JSON...")
save_to_csv(rows, OUTPUT_DIR / "extraction.csv")
save_to_json(rows, OUTPUT_DIR / "extraction.json")

print(f"Termine ! Fichiers crees dans : {OUTPUT_DIR}")
