# export.py
import csv
import json
from pathlib import Path

def save_to_csv(rows, filename="extraction.csv"):
    if not rows:
        return
    filename = Path(filename)
    filename.parent.mkdir(parents=True, exist_ok=True)
    keys = sorted(set(k for row in rows for k in row))
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)

def save_to_json(rows, filename="extraction.json"):
    filename = Path(filename)
    filename.parent.mkdir(parents=True, exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=4)
        
