# 🧠 Braille Keyboard - Python (Windows)

Application Python permettant de saisir du braille via le clavier numérique, de le convertir en texte et de le lire à voix haute grâce à la synthèse vocale Windows (SAPI).

---

# 🚀 Fonctionnalités

- ✋ Saisie braille **séquentielle** (une touche à la fois)
- 🔤 Conversion en alphabet (a → z)
- 🪟 Interface graphique simple avec Tkinter
- 🔊 Lecture vocale du texte (Windows SAPI via pywin32)
- ⏎ Lecture vocale avec la touche `Entrée`
- 🧹 Validation du caractère avec `0`
- ➕ Espace automatique si `0` est pressé à vide
- ❌ Suppression avec la touche `.` (pavé numérique)
  - clic court → supprimer 1 caractère
  - appui long (> 1 seconde) → supprimer tout le texte
- ⚡ Détection clavier stable et robuste (Tkinter events + timers)

---

# 🎮 Comment ça marche ?

## 🧩 Principe

Tu construis une lettre en appuyant **une touche à la fois**, puis tu valides avec `0`.

---

## 📌 Mapping des points braille

7 → point 1  
4 → point 2  
1 → point 3  
8 → point 4  
5 → point 5  
2 → point 6  

---

## ✍️ Exemple d’utilisation

### Saisie de "e"

Appui : 7 + 5  
Validation : 0  
Résultat : e  

---

### Saisie de "n"

Appui : 7 + 1 + 8  
Validation : 0  
Résultat : n  

---

# 🎯 Contrôles

| Touche | Action |
|--------|--------|
| 7 4 1 8 5 2 | Ajout de points braille |
| 0 | Valider la lettre / espace si vide |
| . (pavé numérique) | Supprimer |
| Appui court . | Supprime 1 caractère |
| Appui long . (>1s) | Supprime tout |
| Entrée | Lire le texte à voix haute |

---

# 📦 Installation

## 1. Installer Python

Python 3.10+

---

## 2. Installer les dépendances

pip install pywin32

---

# ⚠️ Important

Windows uniquement (SAPI + Tkinter)

---

# ▶️ Lancer

python main.py

---

# 🧠 Architecture

- Tkinter (UI)
- keyboard events
- after() timers
- SAPI Windows

---

# 🛠️ Améliorations possibles

- feedback sonore
- mode apprentissage
- export texte
- version exe

