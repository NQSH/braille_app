# 🧠 Braille Keyboard - Python (Windows)

Application Python modulaire permettant de saisir du braille via un clavier standard, de convertir les points en texte, et de lire le résultat à voix haute grâce à la synthèse vocale Windows (SAPI).

---

# 🚀 Fonctionnalités

- ✋ Saisie braille **séquentielle** (une touche à la fois)
- 🔤 Conversion en alphabet (a → z)
- 🔢 Entrée des chiffres avec le signe nombre suivi des lettres a-j
- 🪟 Interface graphique simple avec Tkinter
- 🔊 Lecture vocale du texte (Windows SAPI via pywin32)
- ⏎ Lecture vocale avec la touche `G`
- 🧹 Validation du caractère avec `Espace`
- ➕ Espace automatique si la touche de validation est pressée à vide
- ❌ Suppression avec `m`
  - appui court → supprimer 1 caractère
  - appui long (> 1 seconde) → supprimer tout le texte
- ⌨️ Saisie unique en mode `perkins` avec `s d f j k l`
- 🖥️ Affichage centré en plein écran, avec aide sur `V` et référentiel braille sur `N`

---

# 🎮 Modes de saisie

## Mode `perkins`

- s → point 3
- d → point 2
- f → point 1
- j → point 4
- k → point 5
- l → point 6
- `Espace` → valider lettre ou espace
- m → supprimer

## Raccourcis d'affichage

- `V` → afficher ou fermer l'aide des touches en plein écran
- `N` → afficher ou fermer le référentiel braille en plein écran
- `F3` → activer ou désactiver le mode masqué
- `ECHAP` → fermer une vue plein écran ouverte, sinon quitter l'application

---

# 🎯 Entrée des chiffres et symboles

- Saisir le signe nombre (`⠼` / 3-4-5-6) puis la lettre correspondante pour obtenir un chiffre
- Symboles disponibles : `, ; : . ? ! ' - / +`

---

# 📦 Installation

## 1. Installer Python

Python 3.10+

## 2. Installer les dépendances

pip install -r requirements.txt

---

# ▶️ Lancer

python main.py

---

# 🧠 Architecture du projet

- `main.py` : point d'entrée principal
- `ui/gui.py` : interface Tkinter et gestion des événements
- `braille/mapping.py` : conversion des points braille en caractères, chiffres et symboles
- `braille/mode.py` : définition du mode d'entrée Perkins et des touches associées
- `speech/sapi.py` : synthèse vocale Windows avec pywin32

---

# 🛠️ Améliorations possibles

- feedback sonore additionnel
- mode apprentissage interactif
- export du texte saisi
- version exécutable (.exe)

