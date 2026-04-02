import tkinter as tk
from typing import Optional

from braille.mapping import BrailleTranslator
from braille.mode import AVAILABLE_MODES
from speech.sapi import speak


class BrailleApp:
    def __init__(self) -> None:
        self.translator = BrailleTranslator()
        self.mode = AVAILABLE_MODES[1]
        self.current_buffer: set[int] = set()
        self.current_text = ''
        self.delete_job: Optional[str] = None
        self.delete_held = False

        self.root = tk.Tk()
        self.root.title('Braille NumPad - Stable Mode')

        self.label = tk.Label(self.root, text='', font=('Arial', 24), width=30, height=3, bg='white')
        self.label.pack(padx=10, pady=10)

        self.debug_label = tk.Label(self.root, text='', font=('Arial', 12), fg='blue')
        self.debug_label.pack(padx=10, pady=5)

        self.instructions_label = tk.Label(
            self.root,
            text='F2: changer de mode | Entrée: lire | 0/space: valider | l/. : supprimer',
            font=('Arial', 10),
        )
        self.instructions_label.pack(padx=10, pady=5)

        self.root.bind('<KeyPress>', self.on_key_press)
        self.root.bind('<KeyRelease>', self.on_key_release)
        self.root.bind('<Return>', self.on_enter)
        self.root.bind('<F2>', self.on_toggle_mode)

        self.update_ui()

    def run(self) -> None:
        self.root.mainloop()

    def update_ui(self) -> None:
        text = self.current_text
        if self.translator.number_mode:
            text += '⠼'

        self.label.config(text=text)
        self.debug_label.config(
            text=(
                f'Mode: {self.mode.name} | {self.mode.description} | '
                f'Nombre: {self.translator.number_mode} | Buffer: {sorted(self.current_buffer)}'
            )
        )

    def add_dot(self, dot: int) -> None:
        self.current_buffer.add(dot)
        self.update_ui()

    def validate_letter(self) -> None:
        if not self.current_buffer:
            return

        dot_set = frozenset(self.current_buffer)
        char, _ = self.translator.translate(dot_set)
        self.current_buffer.clear()

        if char is not None:
            self.current_text += char

        self.update_ui()

    def add_space(self) -> None:
        self.current_text += ' '
        self.update_ui()

    def delete_short(self) -> None:
        self.current_text = self.current_text[:-1]
        self.update_ui()

    def delete_all(self) -> None:
        self.current_text = ''
        self.current_buffer.clear()
        self.translator.reset()
        self.update_ui()

    def on_key_press(self, event: tk.Event) -> None:
        key = event.keysym

        if key in self.mode.dot_key_map:
            self.add_dot(self.mode.dot_key_map[key])
            return

        if key in self.mode.validate_keys:
            if not self.current_buffer:
                self.add_space()
            else:
                self.validate_letter()
            return

        if key in self.mode.delete_keys:
            self.delete_held = True
            self.delete_job = self.root.after(1000, self._long_delete)

    def on_key_release(self, event: tk.Event) -> None:
        key = event.keysym

        if key in self.mode.delete_keys:
            self.delete_held = False
            if self.delete_job is not None:
                self.root.after_cancel(self.delete_job)
                self.delete_job = None
                self.delete_short()

    def _long_delete(self) -> None:
        if self.delete_held:
            self.delete_all()
        self.delete_job = None

    def on_enter(self, event: tk.Event) -> None:
        speak(self.current_text)

    def on_toggle_mode(self, event: tk.Event) -> None:
        current_index = AVAILABLE_MODES.index(self.mode)
        self.mode = AVAILABLE_MODES[(current_index + 1) % len(AVAILABLE_MODES)]
        self.current_buffer.clear()
        self.translator.reset()
        self.update_ui()
