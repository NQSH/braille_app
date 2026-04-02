import tkinter as tk
from typing import Optional

from braille.mapping import BrailleTranslator, LETTER_MAP, DIGIT_MAP, PUNCTUATION_MAP
from braille.mode import AVAILABLE_MODES
from speech.sapi import speak


SPECIAL_MAP = {
    frozenset({1, 2, 3, 4, 5, 6}): 'ç',
    frozenset({1, 2, 3, 4, 5}): 'è',
    frozenset({1, 2, 3, 4}): 'à',
    frozenset({1, 2, 3}): 'é',
    frozenset({1, 2}): 'ù',
}


def create_rounded_label(parent, bg, fg, radius, width=100, height=50, text='', font=('Arial', 12), pixels_per_char=10):
    if text:
        # Calculate width based on len(text) * pixels_per_char + padding
        width = len(text) * pixels_per_char + 20
        # Height based on font size if not specified
        if height == 50:  # default
            height = font[1] + 10 if len(font) > 1 else 30
    
    canvas = tk.Canvas(parent, width=width, height=height, bg=parent['bg'], highlightthickness=0)
    
    def round_rectangle(x1, y1, x2, y2, radius=radius):
        points = [x1+radius, y1, x2-radius, y1, x2, y1, x2, y1+radius, x2, y2-radius, x2, y2, x2-radius, y2, x1+radius, y2, x1, y2, x1, y2-radius, x1, y1+radius, x1, y1]
        return canvas.create_polygon(points, fill=bg, outline='', smooth=True)
    
    round_rectangle(2, 2, width-2, height-2, radius)
    text_id = canvas.create_text(width/2, height/2, text=text, font=font, fill=fg)
    return canvas, text_id


def create_braille_canvas(parent, dots: frozenset[int], size=20):
    canvas = tk.Canvas(parent, width=2*size, height=3*size, bg='white', highlightthickness=0)
    positions = {
        1: (0, 0),  # left top
        2: (0, 1),  # left middle
        3: (0, 2),  # left bottom
        4: (1, 0),  # right top
        5: (1, 1),  # right middle
        6: (1, 2),  # right bottom
    }
    for i in range(1, 7):
        col, row = positions[i]
        x = col * size + size // 2
        y = row * size + size // 2
        color = 'black' if i in dots else 'white'
        canvas.create_oval(x - size//4, y - size//4, x + size//4, y + size//4, fill=color, outline='black')
    return canvas


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
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_columnconfigure(1, weight=0)  # center narrower
        self.container.grid_columnconfigure(2, weight=1)

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

        # Buffer and number preview
        buffer_frame = tk.Frame(self.main_frame, bg='#2C2C2C')
        buffer_frame.pack(fill='x', pady=5)
        # Left: Buffer fully left
        buffer_title = tk.Label(buffer_frame, text='Buffer', font=('Arial', 12, 'bold'), fg='white', bg='#2C2C2C')
        buffer_title.pack(side='left')
        self.buffer_canvas, self.buffer_text_id = create_rounded_label(buffer_frame, bg='white', fg='#2C2C2C', radius=4, width=120, height=30, text='', font=('Arial', 12, 'bold'))
        self.buffer_canvas.pack(side='left', padx=(10, 0))
        # Right: Mode nombre fully right
        self.number_value = tk.Label(buffer_frame, text='', font=('Arial', 14, 'bold'), bg='#2C2C2C', fg='white')
        self.number_value.pack(side='right')
        number_title = tk.Label(buffer_frame, text='Mode nombre', font=('Arial', 12, 'bold'), fg='white', bg='#2C2C2C')
        number_title.pack(side='right', padx=(0, 10))

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
            perkins_keys = [('S', '1'), ('D', '2'), ('F', '3'), (' ', ' '), ('H', '4'), ('J', '5'), ('K', '6')]
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
            delete_key = 'L'
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

        self.input_canvas.itemconfig(self.input_text_id, text=text)

        # Update mode
        mode_color = '#E0B0FF' if self.mode.name == 'perkins' else '#FFFF99'
        self.mode_label.config(text=self.mode.name.upper(), fg=mode_color)
        self.desc_label.config(text=self.mode.description)

        # Buffer
        self.buffer_canvas.itemconfig(self.buffer_text_id, text=' '.join(map(str, sorted(self.current_buffer))), fill='dodger blue', font=('Arial', 12, 'bold'))

        # Number preview
        status = self.translator.number_mode
        self.number_value.config(text='ACTIVÉ' if status else 'DÉSACTIVÉ', fg='lime' if status else 'orange')

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
                if self.translator.number_mode:
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

    def create_braille_grid(self, parent, mapping: dict, breaks: list = None) -> None:
        if breaks is None:
            breaks = []
        current_row_frame = None
        col = 0
        max_cols = 10  # Adjust as needed
        for dots, char in mapping.items():
            if char in breaks or col == 0:
                current_row_frame = tk.Frame(parent, bg='#2C2C2C')
                current_row_frame.pack(pady=2)
                col = 0
            pair_frame = tk.Frame(current_row_frame, bg='#2C2C2C')
            pair_frame.pack(side='left', padx=5)
            braille_canvas = create_braille_canvas(pair_frame, dots, size=15)
            braille_canvas.pack()
            tk.Label(pair_frame, text=char.upper() if char.isalpha() else char, font=('Arial', 10, 'bold'), fg='white', bg='#2C2C2C').pack()
            col += 1
            if col >= max_cols:
                col = 0

    def create_left_panels(self) -> None:
        # Alphabet top left
        alphabet_frame = tk.Frame(self.left_frame, bg='#2C2C2C')
        alphabet_frame.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)
        tk.Label(alphabet_frame, text='Alphabet', font=('Arial', 14, 'bold'), fg='white', bg='#2C2C2C').pack(pady=(0, 10))
        self.create_braille_grid(alphabet_frame, LETTER_MAP, breaks=['k', 'u'])

        # Numbers bottom left
        numbers_frame = tk.Frame(self.left_frame, bg='#2C2C2C')
        numbers_frame.grid(row=1, column=0, sticky='nsew', padx=10, pady=10)
        tk.Label(numbers_frame, text='Chiffres', font=('Arial', 14, 'bold'), fg='white', bg='#2C2C2C').pack(pady=(0, 10))
        self.create_braille_grid(numbers_frame, DIGIT_MAP)

    def create_right_panels(self) -> None:
        # Special characters top right
        special_frame = tk.Frame(self.right_frame, bg='#2C2C2C')
        special_frame.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)
        tk.Label(special_frame, text='Caractères spéciaux', font=('Arial', 14, 'bold'), fg='white', bg='#2C2C2C').pack(pady=(0, 10))
        self.create_braille_grid(special_frame, SPECIAL_MAP)

        # Punctuation bottom right
        punctuation_frame = tk.Frame(self.right_frame, bg='#2C2C2C')
        punctuation_frame.grid(row=1, column=0, sticky='nsew', padx=10, pady=10)
        tk.Label(punctuation_frame, text='Ponctuation', font=('Arial', 14, 'bold'), fg='white', bg='#2C2C2C').pack(pady=(0, 10))
        self.create_braille_grid(punctuation_frame, PUNCTUATION_MAP)
