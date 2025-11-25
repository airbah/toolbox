# File Toolbox

Application de bureau construite avec [Flet](https://flet.dev/) qui regroupe plusieurs outils autour de la gestion de fichiers et d'images. Une barre de navigation permet d'accéder rapidement aux modules disponibles (renommage, détection de doublons, OCR pour captures d'écran, extraction de palette de couleurs) ainsi qu'aux modules à venir (tri, nettoyage EXIF).

## Fonctionnalités

### Renommer des fichiers
- Sélectionner ou glisser-déposer des fichiers, visualiser leurs noms actuels et les nouveaux noms prévus.
- Ajouter un préfixe/suffixe, faire des remplacements ciblés, ou générer une numérotation automatique pour chaque fichier sélectionné.
- Appliquer les changements et vider la liste en un clic via les actions dédiées.

### Détecter et gérer les doublons
- Choisir un dossier (avec option récursive) et définir une taille minimale avant de lancer le scan.
- Barre de progression et messages d'état pendant les trois phases : découverte, pré-hachage, hachage complet.
- Affichage des groupes de doublons trouvés, sélection manuelle ou intelligente (garder le plus récent/ancien), ouverture directe des fichiers, et suppression vers la corbeille.

### Organiser des captures d'écran par OCR
- Sélection de captures d'écran (via file picker dédié) puis extraction de texte avec Tesseract.
- Choix de la langue OCR et du nombre de mots clés à conserver pour générer automatiquement de nouveaux noms de fichier.
- Aperçu du texte détecté, édition manuelle des nouveaux noms et renommage en lot une fois l'analyse terminée.

### Extraire une palette de couleurs
- Charger une image (JPG/PNG/WebP) et extraire automatiquement un ensemble de couleurs dominantes (2 à 32 couleurs).
- Affichage de l'image avec zoom et pipette : un clic sur le visuel ajoute la couleur au tableau.
- Cartes de couleurs interactives : suppression d'une couleur ou copie du code HEX dans le presse-papiers en un clic.

### Modules à venir
- **File Sorter** : interface prête mais logique métier à compléter.
- **EXIF Cleaner** : écran placeholder en attendant l'implémentation de la suppression des métadonnées.

## Prérequis
- Python 3.10 ou supérieur.
- Dépendances Python listées dans `requirements.txt`.
- Pour l'OCR : installer [Tesseract](https://tesseract-ocr.github.io/) et s'assurer que l'exécutable est dans le `PATH`.

## Installation
```bash
python -m venv .venv
source .venv/bin/activate  # ou .venv\Scripts\activate sous Windows
pip install -r requirements.txt
```

## Lancement de l'application
Exécuter l'application Flet en local :
```bash
python main.py
```
L'interface se lance avec la barre latérale de navigation. Chaque module gère son propre sélecteur de fichiers/dossiers via les composants Flet.

## Arborescence principale
- `main.py` : point d'entrée Flet et navigation entre vues.
- `views/` : composants UI par fonctionnalité (renommage, doublons, OCR, palette, etc.).
- `utils/` : helpers (styles, gestion de fichiers, détection de doublons, OCR).
- `requirements.txt` : dépendances Python.
