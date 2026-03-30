# 🧠 Braille Keyboard - Python (Windows)

Application Python permettant de saisir du braille via le clavier, de le convertir en texte et de le lire à voix haute grâce à la synthèse vocale Windows.

---

# 🚀 Fonctionnalités

- ✋ Saisie braille via touches clavier :
  - `7, 4, 1, 8, 5, 2`
- 🔤 Conversion automatique en alphabet (a → z)
- 🪟 Interface graphique simple avec Tkinter
- 🔊 Lecture vocale du texte (Windows SAPI via pywin32)
- ⏎ Lecture du texte avec la touche `Entrée`
- 🧹 Effacement du texte avec la touche `0`
- ⚡ Détection clavier fiable (mode polling, multi-touches)

---

# 🎮 Comment ça marche ?

Le système utilise un clavier braille simplifié :

## 📌 Correspondance des points


7 → point 1
4 → point 2
1 → point 3
8 → point 4
5 → point 5
2 → point 6


---

## ✍️ Exemple

### Saisie :

7 + 5 → e
7 + 1 + 8 → n


### Résultat :

en


---

# 📦 Installation

## 1. Installer Python

Version recommandée :
- Python 3.10 ou supérieur

---

## 2. Installer les dépendances

Ouvre un terminal et exécute :

```bash
pip install pywin32 keyboard