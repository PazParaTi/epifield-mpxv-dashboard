# export.py
import csv
import json

def save_to_csv(rows, filename="extraction.csv"):
    if not rows:
        return
    keys = sorted(set(k for row in rows for k in row))
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)

def save_to_json(rows, filename="extraction.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=4)
        