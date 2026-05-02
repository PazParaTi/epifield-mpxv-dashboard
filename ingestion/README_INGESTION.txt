Guide d'installation et d'utilisation pour l'extraction de données CRF MPox

Ce projet contient des scripts Python pour extraire des données structurées de fichiers Word (.docx) contenant des formulaires médicaux CRF (Case Report Forms) pour l'épidémie de MPox (Monkeypox).

Prérequis
- Python 3.6 ou supérieur (recommandé : Python 3.8+)
- Accès à un terminal/command prompt

Installation étape par étape pour une installation fraîche de Python

1. Installer Python
   - Téléchargez Python depuis https://www.python.org/downloads/
   - Lors de l'installation, cochez "Add Python to PATH"
   - Vérifiez l'installation : ouvrez un terminal et tapez `python --version`

2. Télécharger ou cloner le projet
   - Placez les fichiers du projet dans un dossier (ex: C:\Projets\CRF_Mpox)
   - Assurez-vous que la structure est :
     CRF_Mpox/
     ├── Script extraction/
     │   ├── main.py
     │   ├── extract_word.py
     │   ├── parsers.py
     │   ├── aggregator.py
     │   ├── export.py
     │   └── readme.txt
     ├── [fichiers .docx des CRF]
     └── .venv/ (sera créé)

3. Créer un environnement virtuel (recommandé)
   - Ouvrez un terminal
   - Naviguez vers le dossier racine du projet : `cd "C:\Projets\CRF_Mpox"`
   - Créez l'environnement virtuel : `python -m venv .venv`
   - Activez l'environnement :
     - Windows : `.venv\Scripts\activate`
     - macOS/Linux : `source .venv/bin/activate`

4. Installer les dépendances
   - Avec l'environnement virtuel activé : `pip install python-docx`

Configuration
- Placez vos fichiers .docx dans le dossier racine (à côté du dossier "Script extraction")
- Les fichiers doivent être au format .docx

Utilisation
1. Ouvrez un terminal
2. Naviguez vers le dossier "Script extraction" : `cd "Script extraction"`
3. Activez l'environnement virtuel si pas déjà fait : `..\.venv\Scripts\activate`
4. Lancez le script : `python main.py`

Le script va :
- Charger tous les fichiers .docx du dossier parent
- Extraire les données via des expressions régulières
- Créer extraction.csv et extraction.json dans le dossier "Script extraction"

Dépannage
- Si "ModuleNotFoundError: No module named 'docx'" : réinstallez python-docx
- Si "No such file or directory" : vérifiez les chemins des fichiers .docx
- Les fichiers temporaires Word (~$...) sont ignorés automatiquement

Personnalisation
- Modifiez parsers.py pour ajouter de nouvelles variables à extraire
- Ajustez les expressions régulières selon vos besoins
