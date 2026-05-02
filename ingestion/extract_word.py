# extract_word.py
import os
from docx import Document

def extract_text_from_docx(filepath):
    """Retourne le texte brut d'un document Word (.docx)."""
    doc = Document(filepath)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return "\n".join(full_text)

def load_all_word_files(folder_path):
    """Charge tous les fichiers Word du dossier et renvoie un dict {filename: text}."""
    data = {}
    for file in os.listdir(folder_path):
        if file.lower().endswith(".docx"):
            fullpath = os.path.join(folder_path, file)
            try:
                data[file] = extract_text_from_docx(fullpath)
            except Exception as e:
                print(f"Erreur lors du chargement de {file}: {e}")
    return data

if __name__ == "__main__":
    folder = "./word_forms"
    docs = load_all_word_files(folder)
    for name, content in docs.items():
        print("=" * 40)
        print(name)
        print(content[:500], "...")