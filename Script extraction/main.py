# main.py
from extract_word import load_all_word_files
from aggregator import aggregate_all_docs
from export import save_to_csv, save_to_json

folder_path = ".."

print("Chargement des fichiers Word...")
docs = load_all_word_files(folder_path)

print("Extraction des données...")
rows = aggregate_all_docs(docs)

print("Export CSV/JSON...")
save_to_csv(rows)
save_to_json(rows)

print("Terminé ! Fichiers créés : extraction.csv et extraction.json")
