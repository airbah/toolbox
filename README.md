# 📦 File Toolbox

Application de bureau Flet regroupant plusieurs outils pour gérer et nettoyer vos fichiers et images. Une barre de navigation latérale vous permet de passer d'un module à l'autre en un clic.

- 🎯 **Productivité** : actions groupées, raccourcis clairs, feedback immédiat.
- 🖼️ **Images** : OCR pour captures d'écran, extraction de palettes, pipette intégrée.
- 🗂️ **Fichiers** : renommage en masse, détection intelligente des doublons.

---

## 🚀 Aperçu rapide
| Module | À quoi ça sert ? | Points forts |
| --- | --- | --- |
| Renommage | Renommer une sélection de fichiers. | Préfixe/suffixe, remplacement ciblé, numérotation auto, vider la liste en un clic. |
| Doublons | Détecter les fichiers identiques dans un dossier. | Scan récursif optionnel, progression détaillée, sélection intelligente (plus récent/ancien), suppression vers corbeille. |
| OCR Screenshots | Organiser des captures d'écran via l'OCR. | Choix de langue, réglage du nombre de mots clés, aperçu du texte détecté, édition manuelle des nouveaux noms. |
| Palette de couleurs | Extraire les couleurs dominantes d'une image. | Support JPG/PNG/WebP, zoom + pipette, copie HEX, suppression d'une couleur. |
| File Sorter (à venir) | Préparer un tri automatique. | Interface prête, logique à finaliser. |
| EXIF Cleaner (à venir) | Nettoyer les métadonnées EXIF. | Écran placeholder en attendant l'implémentation. |

---

## 📥 Installation express
> Python 3.10+ est requis. Assurez-vous que `pip` est disponible dans votre terminal.

```bash
# Cloner le projet
git clone <url-du-repo>
cd toolbox

# Créer un environnement virtuel
python -m venv .venv

# Activer l'environnement
# Windows
.venv\Scripts\Activate.ps1
# macOS / Linux
source .venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
```

### OCR : installer Tesseract
- **Windows** : télécharger la version UB Mannheim depuis la page des [releases GitHub](https://github.com/UB-Mannheim/tesseract/wiki), ajouter Tesseract au `PATH`, puis vérifier avec `tesseract --version`.
- **macOS** : `brew install tesseract` puis, si besoin, installer les packs de langues (`brew install tesseract-lang` ou `brew install tesseract-lang-fra`).

---

## ▶️ Lancer l'application
```bash
# Une fois l'environnement activé
python main.py  # ou python3 main.py sur macOS/Linux
```

L'interface Flet s'ouvre avec la navigation latérale. Chaque module inclut son propre sélecteur de fichiers ou de dossiers.

---

## 🧭 Arborescence
```
main.py            # Point d'entrée Flet et navigation entre vues
views/             # Composants UI par fonctionnalité
utils/             # Helpers (styles, fichiers, doublons, OCR)
requirements.txt   # Dépendances Python
```

---

## 🛠️ Besoin d'aide ?
- Vérifiez que Tesseract est bien installé et accessible depuis votre terminal si l'OCR échoue.
- Sur Windows, exécutez le terminal en mode « Administrator » si l'activation de l'environnement virtuel échoue.
- En cas de souci, ouvrez une issue ou décrivez le module concerné et les actions effectuées.
