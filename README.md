# 📦 File Toolbox

Application de bureau Flet regroupant plusieurs outils pour gérer et nettoyer vos fichiers et images. Une barre de navigation latérale vous permet de passer d'un module à l'autre en un clic.

- 🎯 **Productivité** : actions groupées, raccourcis clairs, feedback immédiat.
- 🖼️ **Images** : OCR pour captures d'écran, extraction de palettes, pipette intégrée, création d'emojis.
- 🗂️ **Fichiers** : renommage en masse, détection intelligente des doublons, tri automatique de factures.
- 🎬 **Vidéo** : enregistrement d'écran avec audio système.

---

## 🚀 Aperçu rapide
| Module | À quoi ça sert ? | Points forts |
| --- | --- | --- |
| Renommage | Renommer une sélection de fichiers. | Préfixe/suffixe, remplacement ciblé, numérotation auto, vider la liste en un clic. |
| Doublons | Détecter les fichiers identiques dans un dossier. | Scan récursif optionnel, progression détaillée, sélection intelligente (plus récent/ancien), suppression vers corbeille. |
| OCR Screenshots | Organiser des captures d'écran via l'OCR. | Choix de langue, réglage du nombre de mots clés, aperçu du texte détecté, édition manuelle des nouveaux noms. |
| Palette de couleurs | Extraire les couleurs dominantes d'une image. | Support JPG/PNG/WebP, zoom + pipette, copie HEX, suppression d'une couleur. |
| Video Recorder | Enregistrer l'écran avec audio système. | Sélection de région, sauvegarde des zones favorites, pause/reprise, gestion des enregistrements. |
| Emoji Maker | Convertir des images en emojis. | Redimensionnement automatique, plusieurs tailles (32-256px), bibliothèque d'emojis sauvegardés. |
| Factures | Trier automatiquement les factures du dossier Téléchargements. | Détection intelligente (mots-clés, montants, TVA), extraction du nom de société, liste de sociétés personnalisable, classement par société. |
| File Sorter (à venir) | Préparer un tri automatique. | Interface prête, logique à finaliser. |
| EXIF Cleaner (à venir) | Nettoyer les métadonnées EXIF. | Écran placeholder en attendant l'implémentation. |

---

## 📥 Installation express

> Python 3.10+ est requis. Assurez-vous que `pip` est disponible dans votre terminal.

### Windows (méthode rapide)

Double-cliquez sur `install.bat` pour créer l'environnement virtuel et installer les dépendances automatiquement, puis utilisez `run.bat` pour lancer l'application.

### Installation manuelle

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

### Windows (méthode rapide)
Double-cliquez sur `run.bat`.

### Manuel
```bash
# Une fois l'environnement activé
python main.py  # ou python3 main.py sur macOS/Linux
```

L'interface Flet s'ouvre avec la navigation latérale. Chaque module inclut son propre sélecteur de fichiers ou de dossiers.

---

## 🧭 Arborescence
```
main.py              # Point d'entrée Flet et navigation entre vues
views/               # Composants UI par fonctionnalité
  ├── renamer_view.py
  ├── sorter_view.py
  ├── duplicates_view.py
  ├── ocr_view.py
  ├── exif_view.py
  ├── color_palette_view.py
  ├── video_recorder_view.py
  ├── emoji_maker_view.py
  └── invoice_sorter_view.py
utils/               # Helpers (styles, fichiers, doublons, OCR, vidéo, emoji, factures)
  ├── styles.py
  ├── file_manager.py
  ├── duplicate_finder.py
  ├── ocr_helper.py
  ├── video_recorder.py
  ├── emoji_maker.py
  ├── invoice_detector.py
  └── settings_manager.py
requirements.txt     # Dépendances Python
install.bat          # Script d'installation Windows
run.bat              # Script de lancement Windows
```

---

## 📦 Dépendances principales
| Package | Usage |
| --- | --- |
| flet | Interface utilisateur |
| Pillow | Manipulation d'images |
| pytesseract | OCR (reconnaissance de texte) |
| colorgram.py | Extraction de palette de couleurs |
| opencv-python | Enregistrement vidéo |
| mss | Capture d'écran |
| pyaudiowpatch | Capture audio système (Windows) |
| send2trash | Suppression sécurisée vers corbeille |
| pdfplumber | Extraction de texte des PDF |
| PyPDF2 | Lecture de fichiers PDF |
| python-docx | Lecture de fichiers Word |

---

## 🛠️ Besoin d'aide ?
- Vérifiez que Tesseract est bien installé et accessible depuis votre terminal si l'OCR échoue.
- Sur Windows, exécutez le terminal en mode « Administrator » si l'activation de l'environnement virtuel échoue.
- Pour l'enregistrement vidéo avec audio, assurez-vous que `pyaudiowpatch` et `pywin32` sont installés.
- En cas de souci, ouvrez une issue ou décrivez le module concerné et les actions effectuées.
