import tkinter as tk
from typing import Optional

from braille.mapping import BrailleTranslator, LETTER_MAP, DIGIT_MAP, PUNCTUATION_MAP
from braille.mode import AVAILABLE_MODES
from speech.sapi import speak
from ui.components import create_rounded_label, create_braille_canvas, create_braille_grid



class BrailleApp:
    def __init__(self) -> None:
        self.translator = BrailleTranslator()
        self.mode = AVAILABLE_MODES[1]
        self.speech_key = 'g' if self.mode.name == 'perkins' else 'Return'
        self.current_buffer: set[int] = set()
        self.current_text = ''
        self.delete_job: Optional[str] = None
        self.delete_held = False

        self.root = tk.Tk()
        self.root.title('Brapp')
        self.root.configure(bg='#2C2C2C')  # dark anthracite gray
        self.root.attributes('-fullscreen', True)  # Full screen

        # Container frame that fills the screen with grid layout
        self.container = tk.Frame(self.root, bg='#2C2C2C')
        self.container.pack(fill='both', expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        # Left, center, right proportional widths 30%/40%/30%
        self.container.grid_columnconfigure(0, weight=3)
        self.container.grid_columnconfigure(1, weight=4)
        self.container.grid_columnconfigure(2, weight=3)

        # Left panel
        self.left_frame = tk.Frame(self.container, bg='#2C2C2C')
        self.left_frame.grid(row=0, column=0, sticky='nsew')
        self.left_frame.grid_rowconfigure(0, weight=1)
        self.left_frame.grid_rowconfigure(1, weight=1)
        self.left_frame.grid_columnconfigure(0, weight=1)

        # Center panel
        self.center_frame = tk.Frame(self.container, bg='#2C2C2C')
        self.center_frame.grid(row=0, column=1, sticky='nsew')

        # Right panel
        self.right_frame = tk.Frame(self.container, bg='#2C2C2C')
        self.right_frame.grid(row=0, column=2, sticky='nsew')
        self.right_frame.grid_rowconfigure(0, weight=1)
        self.right_frame.grid_rowconfigure(1, weight=1)
        self.right_frame.grid_rowconfigure(2, weight=1)
        self.right_frame.grid_rowconfigure(3, weight=1)
        self.right_frame.grid_columnconfigure(0, weight=1)

        # Main frame in center
        self.main_frame = tk.Frame(self.center_frame, bg='#2C2C2C')
        self.main_frame.pack(fill='both', expand=True)

        # Create side panels
        self.create_left_panels()
        self.create_right_panels()

        # Mode de saisie label
        tk.Label(self.main_frame, text='Mode de saisie', font=('Arial', 14), fg='white', bg='#2C2C2C').pack(pady=(0, 5))
        mode_color = '#E0B0FF' if self.mode.name == 'perkins' else '#FFFF99'
        self.mode_label = tk.Label(self.main_frame, text=self.mode.name.upper(), font=('Arial', 20, 'bold'), fg=mode_color, bg='#2C2C2C')
        self.mode_label.pack(pady=(0, 0))

        # Description
        self.desc_label = tk.Label(self.main_frame, text=self.mode.description, font=('Arial', 12), fg='white', bg='#2C2C2C')
        self.desc_label.pack(pady=(0, 10))

        # Text input frame
        self.input_canvas, self.input_text_id = create_rounded_label(self.main_frame, bg='white', fg='black', radius=8, width=600, height=150, text='', font=('Arial', 24))
        self.input_canvas.pack(padx=10, pady=10)

        # Buffer and mode status
        buffer_frame = tk.Frame(self.main_frame, bg='#2C2C2C', width=600, height=50)
        buffer_frame.pack(pady=5)
        buffer_frame.pack_propagate(False)
        # Left: Mode status
        mode_title = tk.Label(buffer_frame, text='Mode', font=('Arial', 12, 'bold'), fg='white', bg='#2C2C2C')
        mode_title.pack(side='left')
        self.mode_value = tk.Label(buffer_frame, text='', font=('Arial', 12, 'bold'), bg='#2C2C2C', fg='white')
        self.mode_value.pack(side='left', padx=(0, 20))
        
        # Right: Buffer fully right
        self.buffer_canvas, self.buffer_text_id = create_rounded_label(buffer_frame, bg='white', fg='#2C2C2C', radius=4, width=120, height=30, text='', font=('Arial', 12, 'bold'))
        self.buffer_canvas.pack(side='right', padx=(10, 0))
        buffer_title = tk.Label(buffer_frame, text='Buffer', font=('Arial', 12, 'bold'), fg='white', bg='#2C2C2C')
        buffer_title.pack(side='right')

        # Mode indications
        self.indications_frame = tk.Frame(self.main_frame, bg='#2C2C2C')
        self.indications_frame.pack(pady=10)
        self.create_indications()

        # Instructions at bottom
        self.instructions_frame = tk.Frame(self.main_frame, bg='#2C2C2C')
        self.instructions_frame.pack(pady=10, fill='x')
        self.center_instructions = tk.Frame(self.instructions_frame, bg='#2C2C2C')
        self.center_instructions.pack(fill='x', padx=100)
        self.create_instructions()

        self.root.bind('<KeyPress>', self.on_key_press)
        self.root.bind('<KeyRelease>', self.on_key_release)
        self.root.bind(f'<{self.speech_key}>', self.on_enter)
        self.root.bind('<F2>', self.on_toggle_mode)
        self.root.bind('<Escape>', self.on_escape)

        self.update_ui()

    def create_indications(self) -> None:
        # Clear existing
        for widget in self.indications_frame.winfo_children():
            widget.destroy()
        if self.mode.name == 'perkins':
            # Keys and numbers vertically aligned
            perkins_keys = [('S', '3'), ('D', '2'), ('F', '1'), (' ', ' '), ('J', '4'), ('K', '5'), ('L', '6')]
            for key, num in perkins_keys:
                if key == ' ':
                    tk.Label(self.indications_frame, text=' ', bg='#2C2C2C').pack(side='left', padx=10)
                else:
                    pair_frame = tk.Frame(self.indications_frame, bg='#2C2C2C')
                    pair_frame.pack(side='left', padx=2)
                    # Key
                    lbl_canvas, _ = create_rounded_label(pair_frame, bg='white', fg='#2C2C2C', radius=4, height=48, text=key, font=('Arial', 16, 'bold'))
                    lbl_canvas.pack()
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
                        lbl_canvas, _ = create_rounded_label(pair_frame, bg='white', fg='#2C2C2C', radius=4, height=48, text=key, font=('Arial', 16, 'bold'))
                        lbl_canvas.pack(side='left', padx=(0,10))  # space between key and num
                        num_lbl = tk.Label(pair_frame, text=num, font=('Arial', 12), fg='white', bg='#2C2C2C')
                        num_lbl.pack(side='right')
                    else:
                        # Num left, key right
                        num_lbl = tk.Label(pair_frame, text=num, font=('Arial', 12), fg='white', bg='#2C2C2C')
                        num_lbl.pack(side='left')
                        lbl_canvas, _ = create_rounded_label(pair_frame, bg='white', fg='#2C2C2C', radius=4, height=48, text=key, font=('Arial', 16, 'bold'))
                        lbl_canvas.pack(side='right', padx=(10,0))  # space between num and key

    def create_instructions(self) -> None:
        # Clear existing
        for widget in self.center_instructions.winfo_children():
            widget.destroy()
        # Determine keys based on mode
        if self.mode.name == 'perkins':
            validate_key = 'SPACE'
            delete_key = 'M'
            speech_key = 'G'
        else:  # numpad
            validate_key = '0'
            delete_key = '.'
            speech_key = 'ENTRÉE'
        instructions = [
            ['Changer de mode', ('F2',)],
            ['Lire', (speech_key,)],
            ['Valider', (validate_key,)],
            ['Supprimer', (delete_key,)]
        ]
        for parts in instructions:
            line_frame = tk.Frame(self.center_instructions, bg='#2C2C2C')
            line_frame.pack(fill='x', pady=5)  # vertical spacing
            action, key_tuple = parts
            tk.Label(line_frame, text=action, font=('Arial', 12, 'bold'), fg='white', bg='#2C2C2C').pack(side='left')
            for key in key_tuple:
                lbl_canvas, _ = create_rounded_label(line_frame, bg='white', fg='#2C2C2C', radius=4, height=30, text=key, font=('Arial', 12, 'bold'))
                lbl_canvas.pack(side='right')

    def run(self) -> None:
        self.root.mainloop()

    def update_ui(self) -> None:
        text = self.current_text
        if self.translator.number_mode:
            text += '⠼'
        if self.translator.capitals_mode:
            text += '⠠'

        self.input_canvas.itemconfig(self.input_text_id, text=text)

        # Update mode
        mode_color = '#E0B0FF' if self.mode.name == 'perkins' else '#FFFF99'
        self.mode_label.config(text=self.mode.name.upper(), fg=mode_color)
        self.desc_label.config(text=self.mode.description)

        # Buffer
        self.buffer_canvas.itemconfig(self.buffer_text_id, text=' '.join(map(str, sorted(self.current_buffer))), fill='dodger blue', font=('Arial', 12, 'bold'))

        # Mode status
        if self.translator.number_mode:
            mode_text = 'NOMBRE'
            mode_color = 'lime'
        elif self.translator.capitals_mode:
            mode_text = 'MAJUSCULE'
            mode_color = 'orange'
        else:
            mode_text = 'AUCUN'
            mode_color = '#A9A9A9'
        self.mode_value.config(text=mode_text, fg=mode_color)

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
                if self.translator.capitals_mode:
                    self.translator.capitals_mode = False
                    self.update_ui()
                elif self.translator.number_mode:
                    self.translator.number_mode = False
                    self.update_ui()
                else:
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
        # Update speech key binding
        old_key = self.speech_key
        self.speech_key = 'g' if self.mode.name == 'perkins' else 'Return'
        if old_key != self.speech_key:
            self.root.unbind(f'<{old_key}>')
            self.root.bind(f'<{self.speech_key}>', self.on_enter)
        self.create_indications()
        self.create_instructions()
        self.update_ui()

    def on_escape(self, event: tk.Event) -> None:
        self.root.destroy()

    def create_left_panels(self) -> None:
        pass

    def create_right_panels(self) -> None:
        # Alphabet top left
        alphabet_frame = tk.Frame(self.right_frame, bg='#2C2C2C')
        alphabet_frame.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)
        tk.Label(alphabet_frame, text='Alphabet', font=('Arial', 14, 'bold'), fg='white', bg='#2C2C2C').pack(pady=(0, 10))
        create_braille_grid(alphabet_frame, LETTER_MAP)

        # Signe majuscule middle left
        special_frame = tk.Frame(self.right_frame, bg='#2C2C2C')
        special_frame.grid(row=1, column=0, sticky='nsew', padx=10, pady=10)

        tk.Label(special_frame, text='Signe majuscule', font=('Arial', 14, 'bold'), fg='white', bg='#2C2C2C').pack(pady=(0, 10))
        create_braille_grid(special_frame, {frozenset({4, 6}): ''})
        
        tk.Label(special_frame, text='Signe numérique', font=('Arial', 14, 'bold'), fg='white', bg='#2C2C2C').pack(pady=(0, 10))
        create_braille_grid(special_frame, {frozenset({6}): ''})

        # Numbers bottom left
        numbers_frame = tk.Frame(self.right_frame, bg='#2C2C2C')
        numbers_frame.grid(row=2, column=0, sticky='nsew', padx=10, pady=10)
        tk.Label(numbers_frame, text='Chiffres', font=('Arial', 14, 'bold'), fg='white', bg='#2C2C2C').pack(pady=(0, 10))
        create_braille_grid(numbers_frame, DIGIT_MAP)

        # Punctuation bottom right
        punctuation_frame = tk.Frame(self.right_frame, bg='#2C2C2C')
        punctuation_frame.grid(row=3, column=0, sticky='nsew', padx=10, pady=10)
        tk.Label(punctuation_frame, text='Ponctuation', font=('Arial', 14, 'bold'), fg='white', bg='#2C2C2C').pack(pady=(0, 10))
        create_braille_grid(punctuation_frame, PUNCTUATION_MAP)

