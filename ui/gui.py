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
        self.root.configure(bg='#2C2C2C')  # dark anthracite gray

        # Main frame with padding
        self.main_frame = tk.Frame(self.root, bg='#2C2C2C')
        self.main_frame.pack(padx=20, pady=20, fill='both', expand=True)

        # Mode de saisie label
        tk.Label(self.main_frame, text='Mode de saisie', font=('Arial', 14), fg='white', bg='#2C2C2C').pack(pady=(0, 5))
        mode_color = '#E0B0FF' if self.mode.name == 'perkins' else '#FFFF99'
        self.mode_label = tk.Label(self.main_frame, text=self.mode.name.upper(), font=('Arial', 20, 'bold'), fg=mode_color, bg='#2C2C2C')
        self.mode_label.pack(pady=(0, 0))

        # Description
        self.desc_label = tk.Label(self.main_frame, text=self.mode.description, font=('Arial', 12), fg='white', bg='#2C2C2C')
        self.desc_label.pack(pady=(0, 10))

        # Text input frame
        self.label = tk.Label(self.main_frame, text='', font=('Arial', 24), width=30, height=3, bg='white', fg='black')
        self.label.pack(padx=10, pady=10)

        # Buffer and number preview
        buffer_frame = tk.Frame(self.main_frame, bg='#2C2C2C')
        buffer_frame.pack(fill='x', pady=5)
        # Left half: Buffer
        left_frame = tk.Frame(buffer_frame, bg='#2C2C2C')
        left_frame.pack(side='left', expand=True, fill='x')
        buffer_title = tk.Label(left_frame, text='Buffer', font=('Arial', 12, 'bold'), fg='white', bg='#2C2C2C')
        buffer_title.pack(side='left')
        self.buffer_value = tk.Label(left_frame, text='', font=('Arial', 12), bg='white', fg='#2C2C2C', padx=5, pady=5)
        self.buffer_value.pack(side='right')
        # Right half: Mode nombre
        right_frame = tk.Frame(buffer_frame, bg='#2C2C2C')
        right_frame.pack(side='right', expand=True, fill='x')
        number_title = tk.Label(right_frame, text='Mode nombre', font=('Arial', 12, 'bold'), fg='white', bg='#2C2C2C')
        number_title.pack(side='left')
        self.number_value = tk.Label(right_frame, text='', font=('Arial', 12), bg='white', fg='#2C2C2C', padx=5, pady=5)
        self.number_value.pack(side='right')

        # Mode indications
        self.indications_frame = tk.Frame(self.main_frame, bg='#2C2C2C')
        self.indications_frame.pack(pady=10)
        self.create_indications()

        # Instructions at bottom
        self.instructions_frame = tk.Frame(self.main_frame, bg='#2C2C2C')
        self.instructions_frame.pack(pady=10, anchor='w')  # align left
        self.create_instructions()

        self.root.bind('<KeyPress>', self.on_key_press)
        self.root.bind('<KeyRelease>', self.on_key_release)
        self.root.bind('<Return>', self.on_enter)
        self.root.bind('<F2>', self.on_toggle_mode)

        self.update_ui()

    def create_indications(self) -> None:
        # Clear existing
        for widget in self.indications_frame.winfo_children():
            widget.destroy()
        if self.mode.name == 'perkins':
            # Keys and numbers vertically aligned
            perkins_keys = [('S', '1'), ('D', '2'), ('F', '3'), (' ', ' '), ('H', '4'), ('J', '5'), ('K', '6')]
            for key, num in perkins_keys:
                if key == ' ':
                    tk.Label(self.indications_frame, text=' ', bg='#2C2C2C').pack(side='left', padx=10)
                else:
                    pair_frame = tk.Frame(self.indications_frame, bg='#2C2C2C')
                    pair_frame.pack(side='left', padx=2)
                    # Key
                    lbl = tk.Label(pair_frame, text=key, font=('Arial', 16, 'bold'), bg='white', fg='#2C2C2C', padx=5, pady=5)
                    lbl.pack()
                    # Number below
                    num_lbl = tk.Label(pair_frame, text=num, font=('Arial', 12), fg='white', bg='#2C2C2C')
                    num_lbl.pack()
        else:
            # Numpad
            numpad_layout = [
                [('7', '1'), ('8', '4')],
                [('4', '2'), ('5', '5')],
                [('1', '3'), ('2', '6')]
            ]
            for row in numpad_layout:
                row_frame = tk.Frame(self.indications_frame, bg='#2C2C2C')
                row_frame.pack(pady=5)  # vertical spacing
                for key, num in row:
                    pair_frame = tk.Frame(row_frame, bg='#2C2C2C')
                    pair_frame.pack(side='left', padx=10)  # horizontal spacing between columns
                    if key in ['8', '5', '2']:
                        # Key left, num right
                        lbl = tk.Label(pair_frame, text=key, font=('Arial', 16, 'bold'), bg='white', fg='#2C2C2C', padx=5, pady=5)
                        lbl.pack(side='left', padx=(0,10))  # space between key and num
                        num_lbl = tk.Label(pair_frame, text=num, font=('Arial', 12), fg='white', bg='#2C2C2C')
                        num_lbl.pack(side='right')
                    else:
                        # Num left, key right
                        num_lbl = tk.Label(pair_frame, text=num, font=('Arial', 12), fg='white', bg='#2C2C2C')
                        num_lbl.pack(side='left')
                        lbl = tk.Label(pair_frame, text=key, font=('Arial', 16, 'bold'), bg='white', fg='#2C2C2C', padx=5, pady=5)
                        lbl.pack(side='right', padx=(10,0))  # space between num and key

    def create_instructions(self) -> None:
        # Clear existing
        for widget in self.instructions_frame.winfo_children():
            widget.destroy()
        # Determine keys based on mode
        if self.mode.name == 'perkins':
            validate_key = 'SPACE'
            delete_key = 'L'
        else:  # numpad
            validate_key = '0'
            delete_key = '.'
        instructions = [
            [('F2',), ': changer de mode'],
            [('ENTRÉE',), ': lire'],
            [(validate_key,), ': valider'],
            [(delete_key,), ': supprimer']
        ]
        for parts in instructions:
            line_frame = tk.Frame(self.instructions_frame, bg='#2C2C2C')
            line_frame.pack(anchor='w', pady=5)  # vertical spacing
            for part in parts:
                if isinstance(part, tuple):
                    for key in part:
                        lbl = tk.Label(line_frame, text=key, font=('Arial', 12, 'bold'), bg='white', fg='#2C2C2C', padx=5, pady=5)
                        lbl.pack(side='left', padx=2)
                else:
                    tk.Label(line_frame, text=part, font=('Arial', 12), fg='white', bg='#2C2C2C').pack(side='left')

    def run(self) -> None:
        self.root.mainloop()

    def update_ui(self) -> None:
        text = self.current_text
        if self.translator.number_mode:
            text += '⠼'

        self.label.config(text=text)

        # Update mode
        mode_color = '#E0B0FF' if self.mode.name == 'perkins' else '#FFFF99'
        self.mode_label.config(text=self.mode.name.upper(), fg=mode_color)
        self.desc_label.config(text=self.mode.description)

        # Buffer
        self.buffer_value.config(text=str(sorted(self.current_buffer)))

        # Number preview
        self.number_value.config(text='Activé' if self.translator.number_mode else 'Désactivé')

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
        self.create_indications()
        self.create_instructions()
        self.update_ui()
