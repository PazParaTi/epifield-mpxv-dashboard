# Upload du projet vers GitHub

Prérequis
- Installer Git for Windows: https://git-scm.com/download/win

Étapes rapides (PowerShell)

```powershell
# config (si non déjà fait)
git config --global user.name "Ton Nom"
git config --global user.email "ton.email@example.com"

cd "d:\université\Année II gea RH\Epifield"
# lancer le script fourni (remote déjà renseigné pour ce repo)
powershell -ExecutionPolicy Bypass -File .\scripts\push_to_github.ps1
```

Si tu veux utiliser une autre URL distante, exécute :

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\push_to_github.ps1 -RemoteUrl "https://github.com/TONCOMPTE/TONREPO.git"
```

Notes
- Le script vérifie si `git` est présent et échoue proprement sinon.
- Vérifie le `.gitignore` pour t'assurer que tu ne commites pas des données sensibles.