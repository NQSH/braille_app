import tkinter as tk
import threading
import win32com.client
import pythoncom

# =========================
# SYNTHÈSE VOCALE (SAPI)
# =========================
def speak(text):
    def run():
        import pythoncom
        pythoncom.CoInitialize()  # 👈 IMPORTANT (corrige ton crash)

        speaker = win32com.client.Dispatch("SAPI.SpVoice")
        speaker.Speak(text)

        pythoncom.CoUninitialize()  # propre fermeture

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
# VARIABLES
# =========================
pressed_keys = set()
active_keys = set()
current_text = ""
validation_job = None

# =========================
# INTERFACE TKINTER
# =========================
root = tk.Tk()
root.title("Braille NumPad (Windows SAPI)")

label = tk.Label(root, text="", font=("Arial", 24), width=30, height=3, bg="white")
label.pack(padx=10, pady=10)

debug_label = tk.Label(root, text="", font=("Arial", 12), fg="blue")
debug_label.pack(padx=10, pady=5)


def update_label():
    label.config(text=current_text)


def update_debug():
    debug_label.config(
        text=f"Touches actives: {active_keys} | Points: {pressed_keys}"
    )


def normalize_key(key):
    """Gère KP_7 ou 7"""
    if key.startswith("KP_"):
        return key.replace("KP_", "")
    return key


# =========================
# GESTION CLAVIER
# =========================
def on_key_press(event):
    global current_text

    key = normalize_key(event.keysym)
    print("PRESS:", key)

    # Effacer texte
    if key == '0':
        current_text = ""
        update_label()
        return

    # Lecture vocale
    if event.keysym == 'Return':
        print("Lecture:", current_text)
        speak(current_text)
        return

    # Braille
    if key in key_to_dot:
        active_keys.add(key)
        pressed_keys.add(key_to_dot[key])
        update_debug()


def on_key_release(event):
    global current_text

    key = normalize_key(event.keysym)
    print("RELEASE:", key)

    if key in key_to_dot:
        active_keys.discard(key)

        # IMPORTANT : on ne valide PLUS immédiatement
        if not active_keys:
            schedule_validation()

def schedule_validation():
    global validation_job

    def validate():
        global pressed_keys, current_text

        if pressed_keys:
            char = braille_map.get(frozenset(pressed_keys), '?')
            print("Lettre:", char)

            current_text += char
            update_label()

            pressed_keys.clear()
            update_debug()

    # annule ancien timer
    if validation_job:
        root.after_cancel(validation_job)

    # attend 80ms avant validation
    validation_job = root.after(80, validate)

# =========================
# BIND EVENTS
# =========================
root.bind("<KeyPress>", on_key_press)
root.bind("<KeyRelease>", on_key_release)

root.mainloop()