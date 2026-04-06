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
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        self.ui_scale = max(0.62, min(1.0, self.screen_width / 1920, self.screen_height / 1080))
        self._compute_layout_metrics()

        # Single full-screen container for the main input area.
        self.container = tk.Frame(self.root, bg='#2C2C2C')
        self.container.pack(fill='both', expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.main_frame = tk.Frame(self.container, bg='#2C2C2C')
        self.main_frame.grid(row=0, column=0, sticky='nsew', padx=self.main_frame_padx, pady=self.main_frame_pady)

        self.mask_overlay = tk.Frame(self.root, bg='black')
        self.mask_message_frame = tk.Frame(self.mask_overlay, bg='black')
        self.mask_message_frame.place(relx=0.5, rely=0.5, anchor='center')
        tk.Label(
            self.mask_message_frame,
            text='Appuyer sur',
            font=self.mask_message_font,
            fg='white',
            bg='black'
        ).pack(side='left', padx=(0, self.overlay_inline_gap))
        self.mask_key_canvas, _ = create_rounded_label(
            self.mask_message_frame,
            bg='white',
            fg='#2C2C2C',
            radius=8,
            height=self.mask_key_height,
            text='B',
            font=self.mask_key_font
        )
        self.mask_key_canvas.pack(side='left', padx=self.overlay_inline_gap)
        tk.Label(
            self.mask_message_frame,
            text='pour quitter le mode masqué',
            font=self.mask_message_font,
            fg='white',
            bg='black'
        ).pack(side='left', padx=(self.overlay_inline_gap, 0))

        self.help_overlay = tk.Frame(self.root, bg='#101010')
        self.help_content = tk.Frame(self.help_overlay, bg='#101010')
        self.help_content.place(relx=0.5, rely=0.5, anchor='center', relwidth=self.help_relwidth, relheight=self.help_relheight)

        self.reference_overlay = tk.Frame(self.root, bg='#161616')
        self.reference_content = tk.Frame(self.reference_overlay, bg='#161616')
        self.reference_content.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.create_help_overlay()
        self.create_reference_overlay()

        self.create_main_layout()
        self._fit_main_layout_if_needed()

        self.root.bind('<KeyPress>', self.on_key_press)
        self.root.bind('<KeyRelease>', self.on_key_release)
        self.root.bind(f'<{self.speech_key}>', self.on_enter)
        self.root.bind('<b>', self.on_toggle_mask)
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
                tk.Label(self.indications_frame, text=' ', bg='#2C2C2C').pack(side='left', padx=self.indication_spacer_gap)
            else:
                pair_frame = tk.Frame(self.indications_frame, bg='#2C2C2C')
                pair_frame.pack(side='left', padx=self.indication_card_gap)
                lbl_canvas, _ = create_rounded_label(pair_frame, bg='white', fg='#2C2C2C', radius=4, height=self.indication_key_height, text=key, font=self.indication_key_font)
                lbl_canvas.pack()
                num_lbl = tk.Label(pair_frame, text=num, font=self.indication_number_font, fg='white', bg='#2C2C2C')
                num_lbl.pack()

    def create_main_layout(self) -> None:
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        tk.Label(self.main_frame, text='Mode de saisie', font=self.mode_caption_font, fg='white', bg='#2C2C2C').pack(pady=(self.section_top_gap, self.section_small_gap))
        mode_color = '#E0B0FF'
        self.mode_label = tk.Label(self.main_frame, text=self.mode.name.upper(), font=self.mode_title_font, fg=mode_color, bg='#2C2C2C')
        self.mode_label.pack(pady=(0, self.section_tight_gap))

        self.desc_label = tk.Label(self.main_frame, text=self.mode.description, font=self.mode_description_font, fg='white', bg='#2C2C2C')
        self.desc_label.pack(pady=(0, self.section_gap))

        self.input_canvas, self.input_text_id = create_rounded_label(
            self.main_frame,
            bg='white',
            fg='black',
            radius=8,
            width=self.main_panel_width,
            height=self.main_input_height,
            text='',
            font=self.input_font
        )
        self.input_canvas.pack(padx=self.canvas_inline_gap, pady=self.section_gap)

        buffer_frame = tk.Frame(self.main_frame, bg='#2C2C2C', width=self.main_panel_width, height=self.status_bar_height)
        buffer_frame.pack(pady=self.section_small_gap)
        buffer_frame.pack_propagate(False)

        mode_title = tk.Label(buffer_frame, text='Mode', font=self.status_font, fg='white', bg='#2C2C2C')
        mode_title.pack(side='left')
        self.mode_value = tk.Label(buffer_frame, text='', font=self.status_font, bg='#2C2C2C', fg='white')
        self.mode_value.pack(side='left', padx=(0, self.status_inline_gap))

        self.buffer_canvas, self.buffer_text_id = create_rounded_label(
            buffer_frame,
            bg='white',
            fg='#2C2C2C',
            radius=4,
            width=self.buffer_width,
            height=self.buffer_height,
            text='',
            font=self.status_font
        )
        self.buffer_canvas.pack(side='right', padx=(self.canvas_inline_gap, 0))
        buffer_title = tk.Label(buffer_frame, text='Buffer', font=self.status_font, fg='white', bg='#2C2C2C')
        buffer_title.pack(side='right')

        self.indications_frame = tk.Frame(self.main_frame, bg='#2C2C2C')
        self.indications_frame.pack(pady=self.section_gap)
        self.create_indications()

        self.shortcuts_frame = tk.Frame(self.main_frame, bg='#2C2C2C')
        self.shortcuts_frame.pack(pady=(self.section_gap, 0))
        self.create_shortcuts_hint()

    def run(self) -> None:
        self.root.mainloop()

    def create_shortcuts_hint(self) -> None:
        for widget in self.shortcuts_frame.winfo_children():
            widget.destroy()

        hint_title = tk.Label(
            self.shortcuts_frame,
            text='Raccourcis plein écran',
            font=self.shortcut_title_font,
            fg='white',
            bg='#2C2C2C'
        )
        hint_title.pack(pady=(0, self.section_small_gap))

        shortcuts = (
            ('Aide des touches', 'V'),
            ('Mode masqué', 'B'),
            ('Référentiel braille', 'N'),
        )
        row = tk.Frame(self.shortcuts_frame, bg='#2C2C2C')
        row.pack()
        for label_text, key in shortcuts:
            card = tk.Frame(row, bg='#2C2C2C')
            card.pack(side='left', padx=self.shortcut_card_gap)
            tk.Label(card, text=label_text, font=self.shortcut_label_font, fg='white', bg='#2C2C2C').pack(pady=(0, self.section_tight_gap))
            key_canvas, _ = create_rounded_label(card, bg='white', fg='#2C2C2C', radius=6, height=self.shortcut_key_height, text=key, font=self.shortcut_key_font)
            key_canvas.pack()

    def create_help_overlay(self) -> None:
        for widget in self.help_content.winfo_children():
            widget.destroy()

        tk.Label(
            self.help_content,
            text='Aide des touches',
            font=self.help_title_font,
            fg='white',
            bg='#101010'
        ).pack(pady=(self.section_top_gap, self.section_gap))

        sections = [
            ('SAISIE', self._get_context_actions()),
            ('FONCTIONS', (('Afficher ou fermer cette aide', 'V'), ('Afficher ou fermer le référentiel braille', 'N'), ('Mode masqué', 'B'))),
            ('AUTRE', (('Fermer l\'application', 'ECHAP'),)),
        ]

        for title, actions in sections:
            section_frame = tk.Frame(self.help_content, bg='#101010')
            section_frame.pack(fill='x', padx=self.help_section_padx, pady=self.section_small_gap)
            tk.Label(section_frame, text=title, font=self.help_section_title_font, fg='white', bg='#101010').pack(anchor='w', pady=(0, self.section_small_gap))
            for action, key in actions:
                line_frame = tk.Frame(section_frame, bg='#101010')
                line_frame.pack(fill='x', pady=self.line_gap)
                tk.Label(line_frame, text=action, font=self.help_line_font, fg='white', bg='#101010').pack(side='left')
                lbl_canvas, _ = create_rounded_label(
                    line_frame,
                    bg='white',
                    fg='#2C2C2C',
                    radius=6,
                    height=self.help_key_height,
                    text=key,
                    font=self.help_key_font
                )
                lbl_canvas.pack(side='right')

        tk.Label(
            self.help_content,
            text='Appuyer sur V pour revenir a la saisie',
            font=self.help_footer_font,
            fg='#CFCFCF',
            bg='#101010'
        ).pack(pady=(self.section_gap, self.section_small_gap))

    def create_reference_overlay(self) -> None:
        for widget in self.reference_content.winfo_children():
            widget.destroy()

        self.reference_content.grid_rowconfigure(0, weight=0)
        self.reference_content.grid_rowconfigure(1, weight=1)
        self.reference_content.grid_rowconfigure(2, weight=0)
        self.reference_content.grid_columnconfigure(0, weight=1)

        # ── Responsive dot size ───────────────────────────────────────────────
        # Estimate real pixel height of a Label for a given font point size.
        # At 96 DPI: 1 pt ≈ 1.33 px; add ~4 px widget padding → factor 1.5 is safe.
        ref_title_h  = int(self.reference_title_font[1] * 1.5) + self._s(28)   # overlay title row
        ref_footer_h = int(self.reference_footer_font[1] * 1.5) + self._s(24)   # footer row
        grid_outer_v = self._s(12) * 2                                       # grid_frame pady
        grid_outer_h = self._s(20) * 2                                       # grid_frame padx
        panel_pad    = self._s(10) * 2                                       # panel padx / pady

        # Available space inside the grid_frame
        grid_area_h  = self.screen_height - ref_title_h - ref_footer_h - grid_outer_v
        grid_area_w  = self.screen_width  - grid_outer_h

        # Available space inside each panel (half-width each)
        panel_w      = grid_area_w // 2 - panel_pad
        left_h       = grid_area_h      - panel_pad   # alphabet: spans all 3 rows
        right_h_one  = grid_area_h // 3 - panel_pad   # one right-column row (chiffres = tightest)

        # Heights consumed by section title labels
        sec_title_h  = int(self.reference_section_title_font[1] * 1.5) + self._s(10)
        # Height consumed by the character label under each braille cell
        cell_lbl_h   = int(self._font(13, 'bold')[1] * 1.4) + 2
        row_pad      = self._s(4)

        # Width constraint: 10 cols, each cell = 2*ds wide + 2*padx padding on sides.
        # With padx ≈ ds/5 → cell slot ≈ ds * 2.4  →  10 * ds * 2.4 = panel_w
        ds_from_w    = int(panel_w / 24)

        # Height constraint — alphabet (3 rows):
        ds_from_ha   = (left_h    - sec_title_h - 3 * cell_lbl_h - 2 * row_pad) // 9

        # Height constraint — chiffres (1 row, tightest right panel):
        ds_from_hc   = (right_h_one - sec_title_h - cell_lbl_h) // 3

        ref_dot      = max(self._s(10), min(ds_from_w, ds_from_ha, ds_from_hc))
        ref_padx     = max(2, ref_dot // 5)
        ref_row_pady = max(1, ref_dot // 8)
        ref_lbl_font = ('Arial', max(8, ref_dot // 2), 'bold')
        # ─────────────────────────────────────────────────────────────────────

        tk.Label(
            self.reference_content,
            text='Référentiel braille',
            font=self.reference_title_font,
            fg='white',
            bg='#161616'
        ).grid(row=0, column=0, pady=(self._s(16), self._s(12)))

        grid_frame = tk.Frame(self.reference_content, bg='#161616')
        grid_frame.grid(row=1, column=0, sticky='nsew', padx=self._s(20), pady=self._s(12))
        grid_frame.grid_columnconfigure(0, weight=1)
        grid_frame.grid_columnconfigure(1, weight=1)
        grid_frame.grid_rowconfigure(0, weight=1)
        grid_frame.grid_rowconfigure(1, weight=1)
        grid_frame.grid_rowconfigure(2, weight=1)

        alphabet_panel = tk.Frame(grid_frame, bg='#161616')
        alphabet_panel.grid(row=0, column=0, rowspan=3, padx=self._s(10), pady=self._s(10), sticky='nsew')
        alphabet_content = tk.Frame(alphabet_panel, bg='#161616')
        alphabet_content.place(relx=0.5, rely=0.5, anchor='center')
        tk.Label(alphabet_content, text='Alphabet', font=self.reference_section_title_font, fg='white', bg='#161616').pack(pady=(0, self._s(10)))
        create_braille_grid(alphabet_content, LETTER_MAP, max_cols=10, dot_size=ref_dot, label_font=ref_lbl_font, item_padx=ref_padx, row_pady=ref_row_pady)

        punctuation_panel = tk.Frame(grid_frame, bg='#161616')
        punctuation_panel.grid(row=0, column=1, padx=self._s(10), pady=self._s(10), sticky='nsew')
        punctuation_content = tk.Frame(punctuation_panel, bg='#161616')
        punctuation_content.place(relx=0.5, rely=0.5, anchor='center')
        tk.Label(punctuation_content, text='Ponctuation', font=self.reference_section_title_font, fg='white', bg='#161616').pack(pady=(0, self._s(10)))
        create_braille_grid(punctuation_content, PUNCTUATION_MAP, max_cols=10, dot_size=ref_dot, label_font=ref_lbl_font, item_padx=ref_padx, row_pady=ref_row_pady)

        numbers_panel = tk.Frame(grid_frame, bg='#161616')
        numbers_panel.grid(row=1, column=1, padx=self._s(10), pady=self._s(10), sticky='nsew')
        numbers_content = tk.Frame(numbers_panel, bg='#161616')
        numbers_content.place(relx=0.5, rely=0.5, anchor='center')
        tk.Label(numbers_content, text='Chiffres', font=self.reference_section_title_font, fg='white', bg='#161616').pack(pady=(0, self._s(10)))
        create_braille_grid(numbers_content, DIGIT_MAP, max_cols=10, dot_size=ref_dot, label_font=ref_lbl_font, item_padx=ref_padx, row_pady=ref_row_pady)

        special_panel = tk.Frame(grid_frame, bg='#161616')
        special_panel.grid(row=2, column=1, padx=self._s(10), pady=self._s(10), sticky='nsew')
        special_content = tk.Frame(special_panel, bg='#161616')
        special_content.place(relx=0.5, rely=0.5, anchor='center')

        tk.Label(special_content, text='Signes', font=self.reference_section_title_font, fg='white', bg='#161616').pack(pady=(0, self._s(10)))

        signs_row = tk.Frame(special_content, bg='#161616')
        signs_row.pack()

        capitals_frame = tk.Frame(signs_row, bg='#161616')
        capitals_frame.pack(side='left', padx=self._s(16))
        tk.Label(capitals_frame, text='Majuscule', font=self.reference_sign_label_font, fg='white', bg='#161616').pack(pady=(0, self._s(8)))
        create_braille_grid(capitals_frame, {frozenset({4, 6}): ''}, max_cols=10, dot_size=ref_dot, label_font=ref_lbl_font, item_padx=ref_padx, row_pady=ref_row_pady)

        number_frame = tk.Frame(signs_row, bg='#161616')
        number_frame.pack(side='left', padx=self._s(16))
        tk.Label(number_frame, text='Numérique', font=self.reference_sign_label_font, fg='white', bg='#161616').pack(pady=(0, self._s(8)))
        create_braille_grid(number_frame, {frozenset({6}): ''}, max_cols=10, dot_size=ref_dot, label_font=ref_lbl_font, item_padx=ref_padx, row_pady=ref_row_pady)

        tk.Label(
            self.reference_content,
            text='Appuyer sur N pour revenir a la saisie',
            font=self.reference_footer_font,
            fg='#D7D7D7',
            bg='#161616'
        ).grid(row=2, column=0, pady=(self._s(8), self._s(16)))

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
        self.buffer_canvas.itemconfig(self.buffer_text_id, text=' '.join(map(str, sorted(self.current_buffer))), fill='dodger blue', font=self.status_font)

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

    def _compute_layout_metrics(self) -> None:
        self.main_frame_padx = self._clamp_int(int(self.screen_width * 0.015), 16, 42)
        self.main_frame_pady = self._clamp_int(int(self.screen_height * 0.014), 12, 28)
        self.main_panel_width = self._clamp_int(int(self.screen_width * 0.9), 860, self.screen_width - (self.main_frame_padx * 2))
        self.main_input_height = self._clamp_int(int(self.screen_height * 0.22), 140, int(self.screen_height * 0.3))
        self.status_bar_height = self._clamp_int(int(self.screen_height * 0.065), 46, 88)
        self.buffer_width = self._clamp_int(int(self.main_panel_width * 0.24), 220, int(self.main_panel_width * 0.32))
        self.buffer_height = self._clamp_int(int(self.status_bar_height * 0.8), 38, 64)

        self.section_top_gap = self._clamp_int(int(self.screen_height * 0.012), 8, 18)
        self.section_gap = self._clamp_int(int(self.screen_height * 0.018), 14, 28)
        self.section_small_gap = self._clamp_int(int(self.screen_height * 0.01), 8, 16)
        self.section_tight_gap = self._clamp_int(int(self.screen_height * 0.007), 4, 10)
        self.line_gap = self._clamp_int(int(self.screen_height * 0.006), 4, 8)
        self.canvas_inline_gap = self._clamp_int(int(self.screen_width * 0.006), 6, 14)
        self.status_inline_gap = self._clamp_int(int(self.screen_width * 0.01), 10, 22)
        self.overlay_inline_gap = self._clamp_int(int(self.screen_width * 0.01), 12, 24)

        self.mode_caption_font = self._screen_font(0.021, 16, 28)
        self.mode_title_font = self._screen_font(0.038, 24, 46, 'bold')
        self.mode_description_font = self._screen_font(0.02, 14, 24)
        self.input_font = self._screen_font(0.031, 20, 40)
        self.status_font = self._screen_font(0.019, 14, 22, 'bold')

        self.indication_key_height = self._clamp_int(int(self.screen_height * 0.092), 64, 112)
        self.indication_card_gap = self._clamp_int(int(self.screen_width * 0.006), 8, 16)
        self.indication_spacer_gap = self._clamp_int(int(self.screen_width * 0.013), 18, 32)
        self.indication_key_font = self._screen_font(0.034, 22, 40, 'bold')
        self.indication_number_font = self._screen_font(0.021, 14, 24)

        self.shortcut_card_gap = self._clamp_int(int(self.screen_width * 0.012), 16, 30)
        self.shortcut_key_height = self._clamp_int(int(self.screen_height * 0.07), 52, 82)
        self.shortcut_title_font = self._screen_font(0.022, 16, 28, 'bold')
        self.shortcut_label_font = self._screen_font(0.019, 14, 24, 'bold')
        self.shortcut_key_font = self._screen_font(0.024, 18, 32, 'bold')

        self.mask_message_font = self._screen_font(0.03, 20, 40, 'bold')
        self.mask_key_font = self._screen_font(0.028, 18, 36, 'bold')
        self.mask_key_height = self._clamp_int(int(self.screen_height * 0.072), 52, 86)

        self.help_relwidth = 0.92 if self.screen_width <= 1440 else 0.88
        self.help_relheight = 0.94
        self.help_section_padx = self._clamp_int(int(self.screen_width * 0.03), 32, 72)
        self.help_title_font = self._screen_font(0.036, 24, 42, 'bold')
        self.help_section_title_font = self._screen_font(0.026, 18, 32, 'bold')
        self.help_line_font = self._screen_font(0.021, 14, 24, 'bold')
        self.help_key_font = self._screen_font(0.021, 14, 24, 'bold')
        self.help_key_height = self._clamp_int(int(self.screen_height * 0.057), 44, 64)
        self.help_footer_font = self._screen_font(0.019, 14, 22)

        self.reference_title_font = self._screen_font(0.038, 24, 44, 'bold')
        self.reference_section_title_font = self._screen_font(0.026, 18, 30, 'bold')
        self.reference_sign_label_font = self._screen_font(0.02, 14, 22, 'bold')
        self.reference_footer_font = self._screen_font(0.019, 14, 22)

        self._fit_main_layout_to_screen()
        self._fit_help_layout_to_screen()

    def _s(self, value: int) -> int:
        return max(1, int(value * self.ui_scale))

    def _clamp_int(self, value: int, min_value: int, max_value: int) -> int:
        return max(min_value, min(value, max_value))

    def _screen_font(self, ratio: float, min_size: int, max_size: int, weight: str = 'normal') -> tuple[str, int] | tuple[str, int, str]:
        size = self._clamp_int(int(self.screen_height * ratio), min_size, max_size)
        if weight == 'normal':
            return ('Arial', size)
        return ('Arial', size, weight)

    def _scale_metric(self, value: int, factor: float, min_value: int) -> int:
        return max(min_value, int(value * factor))

    def _scale_font_tuple(self, font: tuple[str, int] | tuple[str, int, str], factor: float, min_size: int) -> tuple[str, int] | tuple[str, int, str]:
        family = font[0]
        size = max(min_size, int(font[1] * factor))
        if len(font) == 2:
            return (family, size)
        return (family, size, font[2])

    def _font_height(self, font: tuple[str, int] | tuple[str, int, str]) -> int:
        return int(font[1] * 1.5)

    def _estimate_main_content_height(self) -> int:
        total = 0
        total += self._font_height(self.mode_caption_font) + self.section_top_gap + self.section_small_gap
        total += self._font_height(self.mode_title_font) + self.section_tight_gap
        total += self._font_height(self.mode_description_font) + self.section_gap
        total += self.main_input_height + (self.section_gap * 2)
        total += self.status_bar_height + (self.section_small_gap * 2)
        total += self.indication_key_height + self._font_height(self.indication_number_font) + (self.section_gap * 2)
        total += self._font_height(self.shortcut_title_font) + self.section_small_gap
        total += self._font_height(self.shortcut_label_font) + self.shortcut_key_height + self.section_tight_gap
        total += self.section_gap
        return total

    def _estimate_help_content_height(self) -> int:
        sections = [len(self._get_context_actions()), 3, 1]
        total = 0
        total += self._font_height(self.help_title_font) + self.section_top_gap + self.section_gap
        for line_count in sections:
            total += (self.section_small_gap * 2)
            total += self._font_height(self.help_section_title_font)
            total += self.section_small_gap
            total += line_count * (max(self._font_height(self.help_line_font), self.help_key_height) + (self.line_gap * 2))
        total += self._font_height(self.help_footer_font) + self.section_gap + self.section_small_gap
        return total

    def _fit_main_layout_to_screen(self) -> None:
        available_height = self.screen_height - (self.main_frame_pady * 2) - 6
        estimated_height = self._estimate_main_content_height()
        if estimated_height <= available_height:
            return

        factor = max(0.72, min(0.98, available_height / estimated_height))
        self._scale_main_metrics(factor)

    def _fit_main_layout_if_needed(self) -> None:
        for _ in range(3):
            self.root.update_idletasks()
            available_height = self.screen_height - (self.main_frame_pady * 2) - 6
            required_height = self.main_frame.winfo_reqheight()
            if required_height <= available_height:
                return

            factor = max(0.68, min(0.95, available_height / required_height))
            self._scale_main_metrics(factor)
            self.create_main_layout()

    def _scale_main_metrics(self, factor: float) -> None:
        self.section_top_gap = self._scale_metric(self.section_top_gap, factor, 4)
        self.section_gap = self._scale_metric(self.section_gap, factor, 8)
        self.section_small_gap = self._scale_metric(self.section_small_gap, factor, 4)
        self.section_tight_gap = self._scale_metric(self.section_tight_gap, factor, 2)
        self.main_input_height = self._scale_metric(self.main_input_height, factor, 96)
        self.status_bar_height = self._scale_metric(self.status_bar_height, factor, 34)
        self.buffer_height = self._scale_metric(self.buffer_height, factor, 30)
        self.indication_key_height = self._scale_metric(self.indication_key_height, factor, 42)
        self.shortcut_key_height = self._scale_metric(self.shortcut_key_height, factor, 36)
        self.indication_card_gap = self._scale_metric(self.indication_card_gap, factor, 4)
        self.indication_spacer_gap = self._scale_metric(self.indication_spacer_gap, factor, 8)
        self.shortcut_card_gap = self._scale_metric(self.shortcut_card_gap, factor, 8)

        self.mode_caption_font = self._scale_font_tuple(self.mode_caption_font, factor, 11)
        self.mode_title_font = self._scale_font_tuple(self.mode_title_font, factor, 16)
        self.mode_description_font = self._scale_font_tuple(self.mode_description_font, factor, 11)
        self.input_font = self._scale_font_tuple(self.input_font, factor, 14)
        self.status_font = self._scale_font_tuple(self.status_font, factor, 11)
        self.indication_key_font = self._scale_font_tuple(self.indication_key_font, factor, 14)
        self.indication_number_font = self._scale_font_tuple(self.indication_number_font, factor, 11)
        self.shortcut_title_font = self._scale_font_tuple(self.shortcut_title_font, factor, 11)
        self.shortcut_label_font = self._scale_font_tuple(self.shortcut_label_font, factor, 11)
        self.shortcut_key_font = self._scale_font_tuple(self.shortcut_key_font, factor, 12)

    def _fit_help_layout_to_screen(self) -> None:
        available_height = int(self.screen_height * self.help_relheight) - 10
        estimated_height = self._estimate_help_content_height()
        if estimated_height <= available_height:
            return

        self.help_relheight = 1.0
        available_height = self.screen_height - 10
        factor = max(0.72, min(0.98, available_height / estimated_height))

        self.help_section_padx = self._scale_metric(self.help_section_padx, factor, 16)
        self.line_gap = self._scale_metric(self.line_gap, factor, 2)
        self.help_key_height = self._scale_metric(self.help_key_height, factor, 34)
        self.help_title_font = self._scale_font_tuple(self.help_title_font, factor, 18)
        self.help_section_title_font = self._scale_font_tuple(self.help_section_title_font, factor, 14)
        self.help_line_font = self._scale_font_tuple(self.help_line_font, factor, 12)
        self.help_key_font = self._scale_font_tuple(self.help_key_font, factor, 12)
        self.help_footer_font = self._scale_font_tuple(self.help_footer_font, factor, 12)

    def _font(self, size: int, weight: str = 'normal') -> tuple[str, int] | tuple[str, int, str]:
        scaled_size = max(8, self._s(size))
        if weight == 'normal':
            return ('Arial', scaled_size)
        return ('Arial', scaled_size, weight)

