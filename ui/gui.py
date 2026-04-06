import tkinter as tk
from typing import Optional

from braille.mapping import BrailleTranslator, LETTER_MAP, DIGIT_MAP, PUNCTUATION_MAP
from braille.mode import PERKINS_MODE
from speech.sapi import speak
from ui.components import create_rounded_label, create_braille_grid



class BrailleApp:
    def __init__(self) -> None:
        self.translator = BrailleTranslator()
        self.mode = PERKINS_MODE
        self.speech_key = 'g'
        self.masked_mode = False
        self.help_overlay_visible = False
        self.reference_overlay_visible = False
        self.current_buffer: set[int] = set()
        self.current_text = ''
        self.delete_job: Optional[str] = None
        self.delete_held = False

        self.root = tk.Tk()
        self.root.title('Brapp')
        self.root.configure(bg='#2C2C2C')  # dark anthracite gray
        self.root.attributes('-fullscreen', True)  # Full screen

        # Single full-screen container for the main input area.
        self.container = tk.Frame(self.root, bg='#2C2C2C')
        self.container.pack(fill='both', expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.main_frame = tk.Frame(self.container, bg='#2C2C2C')
        self.main_frame.grid(row=0, column=0)

        self.mask_overlay = tk.Frame(self.root, bg='black')
        self.mask_message_frame = tk.Frame(self.mask_overlay, bg='black')
        self.mask_message_frame.place(relx=0.5, rely=0.5, anchor='center')
        tk.Label(
            self.mask_message_frame,
            text='Appuyer sur',
            font=('Arial', 28, 'bold'),
            fg='white',
            bg='black'
        ).pack(side='left', padx=(0, 20))
        self.mask_key_canvas, _ = create_rounded_label(
            self.mask_message_frame,
            bg='white',
            fg='#2C2C2C',
            radius=8,
            height=56,
            text='F3',
            font=('Arial', 24, 'bold')
        )
        self.mask_key_canvas.pack(side='left', padx=20)
        tk.Label(
            self.mask_message_frame,
            text='pour quitter le mode masqué',
            font=('Arial', 28, 'bold'),
            fg='white',
            bg='black'
        ).pack(side='left', padx=(20, 0))

        self.help_overlay = tk.Frame(self.root, bg='#101010')
        self.help_content = tk.Frame(self.help_overlay, bg='#101010')
        self.help_content.place(relx=0.5, rely=0.5, anchor='center')

        self.reference_overlay = tk.Frame(self.root, bg='#161616')
        self.reference_content = tk.Frame(self.reference_overlay, bg='#161616')
        self.reference_content.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.create_help_overlay()
        self.create_reference_overlay()

        # Mode de saisie label
        tk.Label(self.main_frame, text='Mode de saisie', font=('Arial', 14), fg='white', bg='#2C2C2C').pack(pady=(0, 5))
        mode_color = '#E0B0FF'
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

        self.shortcuts_frame = tk.Frame(self.main_frame, bg='#2C2C2C')
        self.shortcuts_frame.pack(pady=(20, 0))
        self.create_shortcuts_hint()

        self.root.bind('<KeyPress>', self.on_key_press)
        self.root.bind('<KeyRelease>', self.on_key_release)
        self.root.bind(f'<{self.speech_key}>', self.on_enter)
        self.root.bind('<F3>', self.on_toggle_mask)
        self.root.bind('<KeyPress-v>', self.on_toggle_help)
        self.root.bind('<KeyPress-V>', self.on_toggle_help)
        self.root.bind('<KeyPress-n>', self.on_toggle_reference)
        self.root.bind('<KeyPress-N>', self.on_toggle_reference)
        self.root.bind('<Escape>', self.on_escape)

        self.update_ui()

    def create_indications(self) -> None:
        # Clear existing
        for widget in self.indications_frame.winfo_children():
            widget.destroy()

        perkins_keys = [('S', '3'), ('D', '2'), ('F', '1'), (' ', ' '), ('J', '4'), ('K', '5'), ('L', '6')]
        for key, num in perkins_keys:
            if key == ' ':
                tk.Label(self.indications_frame, text=' ', bg='#2C2C2C').pack(side='left', padx=10)
            else:
                pair_frame = tk.Frame(self.indications_frame, bg='#2C2C2C')
                pair_frame.pack(side='left', padx=2)
                lbl_canvas, _ = create_rounded_label(pair_frame, bg='white', fg='#2C2C2C', radius=4, height=48, text=key, font=('Arial', 16, 'bold'))
                lbl_canvas.pack()
                num_lbl = tk.Label(pair_frame, text=num, font=('Arial', 12), fg='white', bg='#2C2C2C')
                num_lbl.pack()

    def run(self) -> None:
        self.root.mainloop()

    def create_shortcuts_hint(self) -> None:
        for widget in self.shortcuts_frame.winfo_children():
            widget.destroy()

        hint_title = tk.Label(
            self.shortcuts_frame,
            text='Raccourcis plein écran',
            font=('Arial', 14, 'bold'),
            fg='white',
            bg='#2C2C2C'
        )
        hint_title.pack(pady=(0, 10))

        shortcuts = (
            ('Aide des touches', 'V'),
            ('Référentiel braille', 'N'),
            ('Mode masqué', 'F3'),
        )
        row = tk.Frame(self.shortcuts_frame, bg='#2C2C2C')
        row.pack()
        for label_text, key in shortcuts:
            card = tk.Frame(row, bg='#2C2C2C')
            card.pack(side='left', padx=14)
            tk.Label(card, text=label_text, font=('Arial', 12, 'bold'), fg='white', bg='#2C2C2C').pack(pady=(0, 6))
            key_canvas, _ = create_rounded_label(card, bg='white', fg='#2C2C2C', radius=6, height=42, text=key, font=('Arial', 16, 'bold'))
            key_canvas.pack()

    def create_help_overlay(self) -> None:
        for widget in self.help_content.winfo_children():
            widget.destroy()

        tk.Label(
            self.help_content,
            text='Aide des touches',
            font=('Arial', 30, 'bold'),
            fg='white',
            bg='#101010'
        ).pack(pady=(0, 30))

        sections = [
            ('SAISIE', self._get_context_actions()),
            ('FONCTIONS', (('Afficher ou fermer cette aide', 'V'), ('Afficher ou fermer le référentiel braille', 'N'), ('Mode masqué', 'F3'))),
            ('AUTRE', (('Fermer l\'application', 'ECHAP'),)),
        ]

        for title, actions in sections:
            section_frame = tk.Frame(self.help_content, bg='#101010')
            section_frame.pack(fill='x', pady=10)
            tk.Label(section_frame, text=title, font=('Arial', 18, 'bold'), fg='white', bg='#101010').pack(anchor='w', pady=(0, 10))
            for action, key in actions:
                line_frame = tk.Frame(section_frame, bg='#101010')
                line_frame.pack(fill='x', pady=6)
                tk.Label(line_frame, text=action, font=('Arial', 15, 'bold'), fg='white', bg='#101010').pack(side='left')
                lbl_canvas, _ = create_rounded_label(
                    line_frame,
                    bg='white',
                    fg='#2C2C2C',
                    radius=6,
                    height=38,
                    text=key,
                    font=('Arial', 15, 'bold')
                )
                lbl_canvas.pack(side='right')

        tk.Label(
            self.help_content,
            text='Appuyer sur V pour revenir a la saisie',
            font=('Arial', 14),
            fg='#CFCFCF',
            bg='#101010'
        ).pack(pady=(30, 0))

    def create_reference_overlay(self) -> None:
        for widget in self.reference_content.winfo_children():
            widget.destroy()

        self.reference_content.grid_rowconfigure(0, weight=0)
        self.reference_content.grid_rowconfigure(1, weight=1)
        self.reference_content.grid_rowconfigure(2, weight=0)
        self.reference_content.grid_columnconfigure(0, weight=1)

        tk.Label(
            self.reference_content,
            text='Référentiel braille',
            font=('Arial', 30, 'bold'),
            fg='white',
            bg='#161616'
        ).grid(row=0, column=0, pady=(24, 12))

        grid_frame = tk.Frame(self.reference_content, bg='#161616')
        grid_frame.grid(row=1, column=0, sticky='nsew', padx=30, pady=18)
        grid_frame.grid_columnconfigure(0, weight=1)
        grid_frame.grid_columnconfigure(1, weight=1)
        grid_frame.grid_rowconfigure(0, weight=1)
        grid_frame.grid_rowconfigure(1, weight=1)

        alphabet_panel = tk.Frame(grid_frame, bg='#161616')
        alphabet_panel.grid(row=0, column=0, padx=18, pady=18, sticky='nsew')
        alphabet_content = tk.Frame(alphabet_panel, bg='#161616')
        alphabet_content.place(relx=0.5, rely=0.5, anchor='center')
        tk.Label(alphabet_content, text='Alphabet', font=('Arial', 18, 'bold'), fg='white', bg='#161616').pack(pady=(0, 12))
        create_braille_grid(alphabet_content, LETTER_MAP, max_cols=10)

        numbers_panel = tk.Frame(grid_frame, bg='#161616')
        numbers_panel.grid(row=1, column=0, padx=18, pady=18, sticky='nsew')
        numbers_content = tk.Frame(numbers_panel, bg='#161616')
        numbers_content.place(relx=0.5, rely=0.5, anchor='center')
        tk.Label(numbers_content, text='Chiffres', font=('Arial', 18, 'bold'), fg='white', bg='#161616').pack(pady=(0, 12))
        create_braille_grid(numbers_content, DIGIT_MAP, max_cols=10)

        punctuation_panel = tk.Frame(grid_frame, bg='#161616')
        punctuation_panel.grid(row=0, column=1, padx=18, pady=18, sticky='nsew')
        punctuation_content = tk.Frame(punctuation_panel, bg='#161616')
        punctuation_content.place(relx=0.5, rely=0.5, anchor='center')
        tk.Label(punctuation_content, text='Ponctuation', font=('Arial', 18, 'bold'), fg='white', bg='#161616').pack(pady=(0, 12))
        create_braille_grid(punctuation_content, PUNCTUATION_MAP, max_cols=10)

        special_panel = tk.Frame(grid_frame, bg='#161616')
        special_panel.grid(row=1, column=1, padx=18, pady=18, sticky='nsew')
        special_content = tk.Frame(special_panel, bg='#161616')
        special_content.place(relx=0.5, rely=0.5, anchor='center')
        tk.Label(special_content, text='Signes', font=('Arial', 18, 'bold'), fg='white', bg='#161616').pack(pady=(0, 12))

        signs_row = tk.Frame(special_content, bg='#161616')
        signs_row.pack()

        capitals_frame = tk.Frame(signs_row, bg='#161616')
        capitals_frame.pack(side='left', padx=18)
        tk.Label(capitals_frame, text='Majuscule', font=('Arial', 14, 'bold'), fg='white', bg='#161616').pack(pady=(0, 8))
        create_braille_grid(capitals_frame, {frozenset({4, 6}): ''}, max_cols=10)

        number_frame = tk.Frame(signs_row, bg='#161616')
        number_frame.pack(side='left', padx=18)
        tk.Label(number_frame, text='Numérique', font=('Arial', 14, 'bold'), fg='white', bg='#161616').pack(pady=(0, 8))
        create_braille_grid(number_frame, {frozenset({6}): ''}, max_cols=10)

        tk.Label(
            self.reference_content,
            text='Appuyer sur N pour revenir a la saisie',
            font=('Arial', 14),
            fg='#D7D7D7',
            bg='#161616'
        ).grid(row=2, column=0, pady=(12, 24))

    def update_ui(self) -> None:
        text = self.current_text
        if self.translator.number_mode:
            text += '⠼'
        if self.translator.capitals_mode:
            text += '⠠'

        self.input_canvas.itemconfig(self.input_text_id, text=text)

        # Update mode
        mode_color = '#E0B0FF'
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

    def on_toggle_help(self, event: tk.Event) -> None:
        if self.reference_overlay_visible:
            self.reference_overlay.place_forget()
            self.reference_overlay_visible = False

        self.help_overlay_visible = not self.help_overlay_visible
        if self.help_overlay_visible:
            self.help_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.help_overlay.lift()
            return

        self.help_overlay.place_forget()

    def on_toggle_reference(self, event: tk.Event) -> None:
        if self.help_overlay_visible:
            self.help_overlay.place_forget()
            self.help_overlay_visible = False

        self.reference_overlay_visible = not self.reference_overlay_visible
        if self.reference_overlay_visible:
            self.reference_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.reference_overlay.lift()
            return

        self.reference_overlay.place_forget()

    def on_toggle_mask(self, event: tk.Event) -> None:
        self.masked_mode = not self.masked_mode
        if self.masked_mode:
            self.mask_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.mask_overlay.lift()
            self.mask_overlay.focus_set()
            return

        self.mask_overlay.place_forget()
        self.container.focus_set()

    def on_escape(self, event: tk.Event) -> None:
        if self.help_overlay_visible:
            self.help_overlay.place_forget()
            self.help_overlay_visible = False
            return

        if self.reference_overlay_visible:
            self.reference_overlay.place_forget()
            self.reference_overlay_visible = False
            return

        self.root.destroy()

    def _get_context_actions(self) -> tuple[tuple[str, str], ...]:
        return (
            ('Valider', 'SPACE'),
            ('Supprimer', 'M'),
            ('Lire', 'G'),
        )

