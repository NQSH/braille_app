# 🧠 Braille Keyboard - Python (Windows)

Application Python modulaire permettant de saisir du braille via un clavier standard, de convertir les points en texte, et de lire le résultat à voix haute grâce à la synthèse vocale Windows (SAPI).

---

# 🚀 Fonctionnalités

- ✋ Saisie braille **séquentielle** (une touche à la fois)
- 🔤 Conversion en alphabet (a → z)
- 🔢 Entrée des chiffres avec le signe nombre suivi des lettres a-j
- 🪟 Interface graphique simple avec Tkinter
- 🔊 Lecture vocale du texte (Windows SAPI via pywin32)
- ⏎ Lecture vocale avec la touche `Entrée`
- 🧹 Validation du caractère avec `0` ou `Espace`
- ➕ Espace automatique si la touche de validation est pressée à vide
- ❌ Suppression avec `.` / `BackSpace` ou `l` selon le mode
  - appui court → supprimer 1 caractère
  - appui long (> 1 seconde) → supprimer tout le texte
- 🔁 Deux modes de saisie
  - `numpad` : clavier numérique classique
  - `perkins` : saisie type Perkins avec `s d f h j k`

---

# 🎮 Modes de saisie

## Mode `numpad`

- 7 → point 1
- 4 → point 2
- 1 → point 3
- 8 → point 4
- 5 → point 5
- 2 → point 6
- 0 → valider lettre ou espace
- . / BackSpace / Delete → supprimer

## Mode `perkins`

- s → point 1
- d → point 2
- f → point 3
- h → point 4
- j → point 5
- k → point 6
- `Espace` → valider lettre ou espace
- l → supprimer

## Switcher de mode

- `F2` : changer de mode entre `numpad` et `perkins`

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
- `braille/mode.py` : définition des modes d'entrée et des touches associées
- `speech/sapi.py` : synthèse vocale Windows avec pywin32

---

# 🛠️ Améliorations possibles

- feedback sonore additionnel
- mode apprentissage interactif
- export du texte saisi
- version exécutable (.exe)

