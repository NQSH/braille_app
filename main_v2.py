import tkinter as tk
import threading
import keyboard
import win32com.client
import pythoncom

# =========================
# VOIX WINDOWS (SAPI)
# =========================
def speak(text):
    def run():
        pythoncom.CoInitialize()
        speaker = win32com.client.Dispatch("SAPI.SpVoice")
        speaker.Speak(text)
        pythoncom.CoUninitialize()

    threading.Thread(target=run, daemon=True).start()


# =========================
# CONFIG BRAILLE
# =========================
key_to_dot = {
    '7': 1,
    '4': 2,
    '1': 3,
    '8': 4,
    '5': 5,
    '2': 6
}

braille_map = {
    frozenset([1]): 'a',
    frozenset([1,2]): 'b',
    frozenset([1,4]): 'c',
    frozenset([1,4,5]): 'd',
    frozenset([1,5]): 'e',
    frozenset([1,2,4]): 'f',
    frozenset([1,2,4,5]): 'g',
    frozenset([1,2,5]): 'h',
    frozenset([2,4]): 'i',
    frozenset([2,4,5]): 'j',
    frozenset([1,3]): 'k',
    frozenset([1,2,3]): 'l',
    frozenset([1,3,4]): 'm',
    frozenset([1,3,4,5]): 'n',
    frozenset([1,3,5]): 'o',
    frozenset([1,2,3,4]): 'p',
    frozenset([1,2,3,4,5]): 'q',
    frozenset([1,2,3,5]): 'r',
    frozenset([2,3,4]): 's',
    frozenset([2,3,4,5]): 't',
    frozenset([1,3,6]): 'u',
    frozenset([1,2,3,6]): 'v',
    frozenset([2,4,5,6]): 'w',
    frozenset([1,3,4,6]): 'x',
    frozenset([1,3,4,5,6]): 'y',
    frozenset([1,3,5,6]): 'z'
}


# =========================
# ETAT GLOBAL
# =========================
pressed_keys = set()
current_text = ""


# =========================
# UI TKINTER
# =========================
root = tk.Tk()
root.title("Braille Keyboard - Windows")

label = tk.Label(root, text="", font=("Arial", 24), width=30, height=3, bg="white")
label.pack(padx=10, pady=10)

debug = tk.Label(root, text="", font=("Arial", 12), fg="blue")
debug.pack(padx=10, pady=5)


def update_ui():
    debug.config(text=f"Points actifs: {pressed_keys}")
    label.config(text=current_text)


# =========================
# LOGIQUE BRAILLE (POLLING FIABLE)
# =========================
def loop():
    global current_text, pressed_keys

    while True:
        active = set()

        # lecture état clavier réel
        for k, dot in key_to_dot.items():
            if keyboard.is_pressed(k):
                active.add(dot)

        if active:
            pressed_keys = active

        # validation quand aucune touche appuyée
        if not any(keyboard.is_pressed(k) for k in key_to_dot.keys()):
            if pressed_keys:
                char = braille_map.get(frozenset(pressed_keys), '?')
                current_text += char
                pressed_keys = set()
                update_ui()

        update_ui()


# =========================
# COMMANDES
# =========================
def on_enter():
    speak(current_text)


def on_clear():
    global current_text
    current_text = ""
    update_ui()


keyboard.add_hotkey("enter", on_enter)
keyboard.add_hotkey("0", on_clear)


# =========================
# START THREAD INPUT
# =========================
threading.Thread(target=loop, daemon=True).start()

root.mainloop()