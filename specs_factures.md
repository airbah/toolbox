# Spécifications - Application de Tri Automatique de Factures

## 1. Objectif

Développer une application capable de :
- Scanner le dossier **Téléchargements** de l'utilisateur (Windows et macOS)
- Détecter automatiquement les documents qui sont des **factures**
- Déplacer ces factures vers un dossier dédié `factures/`
- Organiser les factures dans des **sous-dossiers** nommés d'après la société émettrice

---

## 2. Chemins des dossiers

### 2.1 Dossier source (Téléchargements)
| OS | Chemin |
|---------|--------|
| Windows | `C:\Users\{username}\Downloads` |
| macOS | `/Users/{username}/Downloads` |

### 2.2 Dossier destination
Le dossier `factures/` sera créé **à l'intérieur** du dossier Téléchargements :
- Windows : `C:\Users\{username}\Downloads\factures\`
- macOS : `/Users/{username}/Downloads/factures/`

### 2.3 Structure des sous-dossiers
```
Téléchargements/
└── factures/
    ├── Amazon/
    │   ├── facture_2024-01-15.pdf
    │   └── facture_2024-02-20.pdf
    ├── Orange/
    │   └── facture_janvier.pdf
    ├── EDF/
    │   └── releve_2024.pdf
    └── Inconnu/
        └── document_sans_societe.pdf
```

---

## 3. Types de fichiers supportés

| Format | Extension | Méthode d'extraction |
|--------|-----------|---------------------|
| PDF | `.pdf` | Extraction de texte (PyPDF2, pdfplumber) + OCR si nécessaire |
| Images | `.jpg`, `.jpeg`, `.png` | OCR (Tesseract / pytesseract) |
| Word | `.docx` | python-docx |

---

## 4. Détection des factures

### 4.1 Critères de détection
L'application doit identifier un document comme **facture** s'il contient au moins **2 des éléments suivants** :

| Critère | Mots-clés / Patterns |
|---------|---------------------|
| Mention explicite | `facture`, `invoice`, `reçu`, `receipt`, `bon de commande` |
| Numéro de facture | `N° facture`, `Invoice #`, `Facture n°`, patterns regex `[A-Z]{0,3}[-]?\d{4,}` |
| Montant TTC/HT | `Total TTC`, `Total HT`, `Montant`, `Amount`, patterns avec `€`, `$`, `EUR` |
| TVA | `TVA`, `VAT`, patterns de taux `20%`, `10%`, `5.5%` |
| Date de facturation | `Date de facture`, `Date d'émission`, `Invoice date` |
| SIRET/SIREN | Pattern `\d{9}` ou `\d{14}` |
| Mentions légales | `RCS`, `SARL`, `SAS`, `SA`, `EURL` |

### 4.2 Score de confiance
- Chaque critère trouvé ajoute des points au score
- Seuil minimum pour considérer un document comme facture : **60%**

---

## 5. Extraction du nom de la société

### 5.1 Stratégies d'extraction (par ordre de priorité)

1. **En-tête du document** : Analyser les premières lignes (généralement logo/nom en haut)
2. **Après mentions légales** : Texte suivant `SARL`, `SAS`, `SA`, etc.
3. **Avant le SIRET** : Le nom précède souvent le numéro SIRET
4. **Domaine email** : Extraire depuis les adresses email présentes (ex: `contact@amazon.fr` → `Amazon`)
5. **Base de données de sociétés connues** : Liste prédéfinie des entreprises courantes

### 5.2 Normalisation du nom
- Supprimer les caractères spéciaux : `Amazon.fr S.A.R.L.` → `Amazon`
- Uniformiser la casse : Première lettre majuscule
- Gérer les variations : `ORANGE`, `Orange SA`, `Orange France` → `Orange`

### 5.3 Cas par défaut
Si aucune société n'est détectée → déplacer dans `factures/Inconnu/`

---

## 6. Interface utilisateur

### 6.1 Option 1 : Intégration dans l'application Toolbox existante
Créer une nouvelle vue `invoice_sorter_view.py` avec :

| Élément | Description |
|---------|-------------|
| Bouton "Scanner" | Lance l'analyse du dossier Téléchargements |
| Liste des fichiers | Affiche les fichiers détectés avec leur statut |
| Prévisualisation | Affiche le contenu/aperçu du document sélectionné |
| Société détectée | Champ modifiable pour corriger si nécessaire |
| Bouton "Trier" | Déplace les fichiers vers les sous-dossiers |
| Progression | Barre de progression pendant le traitement |
| Journal | Log des actions effectuées |

### 6.2 Fonctionnalités additionnelles
- [ ] Mode automatique : tri sans validation manuelle
- [ ] Mode manuel : validation de chaque facture avant déplacement
- [ ] Historique des fichiers traités
- [ ] Annulation du dernier déplacement

---

## 7. Architecture technique

### 7.1 Nouveaux fichiers à créer

```
toolbox/
├── utils/
│   └── invoice_detector.py    # Logique de détection des factures
├── views/
│   └── invoice_sorter_view.py # Interface graphique
└── data/
    └── known_companies.json   # Base de sociétés connues (optionnel)
```

### 7.2 Dépendances Python

```python
# À ajouter dans requirements.txt
PyPDF2>=3.0.0          # Extraction texte PDF
pdfplumber>=0.9.0      # Alternative plus robuste pour PDF
pytesseract>=0.3.10    # OCR pour images et PDF scannés
Pillow>=9.0.0          # Manipulation d'images
python-docx>=0.8.11    # Lecture fichiers Word
```

### 7.3 Dépendance système
- **Tesseract OCR** doit être installé sur le système
  - Windows : `choco install tesseract` ou installateur manuel
  - macOS : `brew install tesseract`

---

## 8. Flux de traitement

```
┌─────────────────────────────────────────────────────────────────┐
│                    FLUX DE TRAITEMENT                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. SCAN DU DOSSIER TÉLÉCHARGEMENTS                            │
│     └─→ Lister tous les fichiers (.pdf, .jpg, .png, .docx)     │
│                                                                 │
│  2. POUR CHAQUE FICHIER                                        │
│     ├─→ Extraire le texte (PDF reader ou OCR)                  │
│     ├─→ Analyser le contenu                                    │
│     ├─→ Calculer le score "facture"                            │
│     └─→ Si score >= 60% → marquer comme facture                │
│                                                                 │
│  3. POUR CHAQUE FACTURE DÉTECTÉE                               │
│     ├─→ Extraire le nom de la société                          │
│     ├─→ Normaliser le nom                                      │
│     └─→ Créer le sous-dossier si nécessaire                    │
│                                                                 │
│  4. DÉPLACEMENT                                                │
│     ├─→ Déplacer le fichier vers factures/{société}/           │
│     └─→ Logger l'action                                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 9. Gestion des erreurs

| Erreur | Action |
|--------|--------|
| Fichier corrompu | Logger l'erreur, passer au suivant |
| PDF protégé par mot de passe | Signaler à l'utilisateur |
| OCR échoue | Tenter extraction alternative, sinon ignorer |
| Nom de société non détecté | Déplacer vers `Inconnu/` |
| Conflit de nom de fichier | Renommer avec suffixe `_1`, `_2`, etc. |
| Droits insuffisants | Afficher message d'erreur explicite |

---

## 10. Sécurité et bonnes pratiques

- [ ] Ne jamais supprimer les fichiers originaux (uniquement déplacer)
- [ ] Créer une sauvegarde/log des déplacements pour permettre l'annulation
- [ ] Valider les chemins pour éviter les path traversal
- [ ] Limiter la taille des fichiers analysés (ex: max 50 Mo)
- [ ] Timeout pour l'OCR (éviter blocage sur fichiers volumineux)

---

## 11. Tests à prévoir

| Test | Description |
|------|-------------|
| Test unitaire détection | Vérifier la détection sur échantillons de factures |
| Test extraction société | Vérifier l'extraction correcte des noms |
| Test normalisation | Vérifier la normalisation des noms de sociétés |
| Test déplacement | Vérifier les déplacements de fichiers |
| Test multiplateforme | Valider sur Windows et macOS |
| Test performance | Mesurer le temps sur un grand nombre de fichiers |

---

## 12. Évolutions futures (hors scope initial)

- [ ] Extraction de la date de facture pour organisation chronologique
- [ ] Extraction du montant pour statistiques
- [ ] Export CSV/Excel des factures traitées
- [ ] Intégration avec un service cloud (Google Drive, Dropbox)
- [ ] Reconnaissance de factures par ML (modèle entraîné)
- [ ] Support d'autres langues (anglais, allemand, espagnol)
- [ ] Notification automatique quand nouvelles factures détectées
- [ ] Configuration du dossier source/destination personnalisable

---

## 13. Priorités de développement

### Phase 1 - MVP (Minimum Viable Product)
1. Extraction de texte des PDF
2. Détection basique des factures (mots-clés)
3. Extraction du nom de société
4. Déplacement des fichiers
5. Interface minimale dans Toolbox

### Phase 2 - Améliorations
1. Support OCR pour images/PDF scannés
2. Amélioration de la détection (score de confiance)
3. Mode automatique vs manuel
4. Historique et annulation

### Phase 3 - Fonctionnalités avancées
1. Base de données de sociétés connues
2. Support fichiers Word
3. Export des données
4. Configuration avancée

---

*Document créé le : 5 décembre 2024*
*Version : 1.0*

