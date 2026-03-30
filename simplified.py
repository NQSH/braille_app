import tkinter as tk
import threading
import time
import win32com.client
import pythoncom


# =========================
# SYNTHÈSE VOCALE
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
# VARIABLES
# =========================
current_buffer = set()
current_text = ""

delete_job = None
delete_held = False


# =========================
# UI
# =========================
root = tk.Tk()
root.title("Braille NumPad - Stable Mode")

label = tk.Label(root, text="", font=("Arial", 24), width=30, height=3, bg="white")
label.pack(padx=10, pady=10)

debug_label = tk.Label(root, text="", font=("Arial", 12), fg="blue")
debug_label.pack(padx=10, pady=5)


def update_ui():
    label.config(text=current_text)
    debug_label.config(text=f"Buffer: {sorted(current_buffer)}")


# =========================
# BRAILLE LOGIC
# =========================
def add_dot(dot):
    current_buffer.add(dot)
    update_ui()


def validate_letter():
    global current_text, current_buffer

    if current_buffer:
        char = braille_map.get(frozenset(current_buffer), '?')
        current_text += char
        current_buffer.clear()
        update_ui()


def add_space():
    global current_text
    current_text += " "
    update_ui()


# =========================
# DELETE LOGIC
# =========================
def delete_short():
    global current_text
    current_text = current_text[:-1]
    update_ui()


def delete_all():
    global current_text, current_buffer
    current_text = ""
    current_buffer.clear()
    update_ui()


# =========================
# KEY HANDLING
# =========================
def on_key_press(event):
    global delete_job, delete_held

    key = event.keysym

    # -------------------------
    # BRAILLE INPUT
    # -------------------------
    if key in ['7', '4', '1', '8', '5', '2']:
        add_dot(key_to_dot[key])

    # -------------------------
    # VALIDATE / SPACE
    # -------------------------
    elif key == '0':
        if not current_buffer:
            add_space()
        else:
            validate_letter()

    # -------------------------
    # DELETE (.)
    # -------------------------
    elif key in ['BackSpace', 'period', 'KP_Decimal', 'Delete']:
        delete_held = True

        def long_delete():
            global delete_held
            if delete_held:
                delete_all()

        delete_job = root.after(1000, long_delete)


def on_key_release(event):
    global delete_job, delete_held

    key = event.keysym

    if key in ['BackSpace', 'period', 'KP_Decimal', 'Delete']:
        delete_held = False

        if delete_job:
            root.after_cancel(delete_job)
            delete_job = None

        delete_short()


# =========================
# VOICE
# =========================
def on_enter(event):
    speak(current_text)


# =========================
# BIND EVENTS
# =========================
root.bind("<KeyPress>", on_key_press)
root.bind("<KeyRelease>", on_key_release)
root.bind("<Return>", on_enter)

root.mainloop()