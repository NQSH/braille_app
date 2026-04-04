import json
import os
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import winreg
import winsound


APP_EVENTS_PATH = r'AppEvents\Schemes\Apps\.Default'
EVENT_LABELS_PATH = r'AppEvents\EventLabels'
SAVED_SOUNDS_FILE = Path(__file__).with_name('braille_sound_library.json')


def _read_registry_value(root, path: str) -> str:
    try:
        with winreg.OpenKey(root, path) as key:
            value, _ = winreg.QueryValueEx(key, '')
            return value
    except FileNotFoundError:
        return ''


def _read_event_label(event_name: str) -> str:
    label_path = fr'{EVENT_LABELS_PATH}\{event_name}'
    label = _read_registry_value(winreg.HKEY_CURRENT_USER, label_path)
    if not label:
        label = _read_registry_value(winreg.HKEY_LOCAL_MACHINE, label_path)
    return label or event_name


def list_windows_default_sounds() -> list[dict[str, str]]:
    sounds: list[dict[str, str]] = []

    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, APP_EVENTS_PATH) as sounds_key:
        index = 0
        while True:
            try:
                event_name = winreg.EnumKey(sounds_key, index)
            except OSError:
                break

            event_path = f'{APP_EVENTS_PATH}\\{event_name}'
            default_value = _read_registry_value(winreg.HKEY_CURRENT_USER, f'{event_path}\\.Default')
            current_value = _read_registry_value(winreg.HKEY_CURRENT_USER, f'{event_path}\\.Current')

            sounds.append(
                {
                    'event': event_name,
                    'label': _read_event_label(event_name),
                    'name': f'{_read_event_label(event_name)} ({event_name})',
                    'default': default_value,
                    'current': current_value,
                }
            )
            index += 1

    return sorted(sounds, key=lambda sound: sound['label'].lower())


def _resolve_sound_path(sound: dict[str, str]) -> str:
    selected_path = sound.get('current') or sound.get('default') or ''
    if not selected_path or selected_path == '.None':
        return ''
    return os.path.expandvars(selected_path)


def play_sound(sound: dict[str, str]) -> None:
    sound_path = _resolve_sound_path(sound)
    if not sound_path:
        raise FileNotFoundError('Aucun fichier son n est associe a cet evenement.')
    if not os.path.exists(sound_path):
        raise FileNotFoundError(f'Fichier introuvable : {sound_path}')
    winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)


def _normalize_saved_sound_entry(item: dict[str, object]) -> tuple[dict[str, str] | None, bool]:
    event_name = str(item.get('event', '')).strip()
    label = str(item.get('label', '')).strip()
    if not event_name or not label:
        return None, False

    name = str(item.get('name', f'{label} ({event_name})')).strip() or f'{label} ({event_name})'
    default = str(item.get('default', '')).strip()
    current = str(item.get('current', '')).strip()
    comment = str(item.get('comment', '')).strip()

    normalized = {
        'event': event_name,
        'label': label,
        'name': name,
        'default': default,
        'current': current,
        'comment': comment,
    }
    migrated = any(key not in item for key in ('name', 'default', 'current', 'comment'))
    return normalized, migrated


def load_saved_sounds() -> list[dict[str, str]]:
    if not SAVED_SOUNDS_FILE.exists():
        return []

    try:
        with SAVED_SOUNDS_FILE.open('r', encoding='utf-8') as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError):
        return []

    if not isinstance(data, list):
        return []

    sounds: list[dict[str, str]] = []
    migrated = False
    for item in data:
        if not isinstance(item, dict):
            continue
        normalized_sound, normalized_migrated = _normalize_saved_sound_entry(item)
        if normalized_sound is None:
            continue
        sounds.append(normalized_sound)
        migrated = migrated or normalized_migrated

    if migrated:
        save_saved_sounds(sounds)

    return sounds


def save_saved_sounds(sounds: list[dict[str, str]]) -> None:
    with SAVED_SOUNDS_FILE.open('w', encoding='utf-8') as file:
        json.dump(sounds, file, indent=2, ensure_ascii=False)


def make_saved_sound_entry(sound: dict[str, str]) -> dict[str, str]:
    return {
        'event': sound['event'],
        'label': sound['label'],
        'name': sound.get('name', f"{sound['label']} ({sound['event']})"),
        'default': sound.get('default', ''),
        'current': sound.get('current', ''),
        'comment': sound.get('comment', ''),
    }


class SoundManagerApp:
    def __init__(self) -> None:
        self.sounds = list_windows_default_sounds()
        self.lookup = {sound['name']: sound for sound in self.sounds}
        self.saved_window: tk.Toplevel | None = None
        self.saved_list_frame: ttk.Frame | None = None

        self.root = tk.Tk()
        self.root.title('Gestionnaire de sons Brapp')
        self.root.geometry('760x280')
        self.root.configure(padx=20, pady=20)

        self.selected_label = tk.StringVar()
        self.selected_event = tk.StringVar()
        self.selected_path = tk.StringVar()
        self.selected_comment = tk.StringVar()

        self._build_main_window()
        if self.sounds:
            self.selected_label.set(self.sounds[0]['name'])
            self.update_selection()

    def _build_main_window(self) -> None:
        ttk.Label(self.root, text='Son Windows').pack(anchor='w')
        combo = ttk.Combobox(
            self.root,
            textvariable=self.selected_label,
            values=list(self.lookup.keys()),
            state='readonly',
            width=76,
        )
        combo.pack(fill='x', pady=(6, 14))
        combo.bind('<<ComboboxSelected>>', self.update_selection)

        ttk.Label(self.root, text='Identifiant').pack(anchor='w')
        ttk.Label(self.root, textvariable=self.selected_event).pack(anchor='w', pady=(2, 10))

        ttk.Label(self.root, text='Fichier joue').pack(anchor='w')
        ttk.Label(self.root, textvariable=self.selected_path, wraplength=700).pack(anchor='w', pady=(2, 16))

        ttk.Label(self.root, text='Commentaire pour l enregistrement').pack(anchor='w')
        ttk.Entry(self.root, textvariable=self.selected_comment, width=76).pack(fill='x', pady=(6, 16))

        buttons_frame = ttk.Frame(self.root)
        buttons_frame.pack(anchor='w')
        ttk.Button(buttons_frame, text='Jouer le son sélectionné', command=self.on_play_selected).pack(side='left')
        ttk.Button(buttons_frame, text='Ajouter le son à la liste', command=self.on_add_selected).pack(side='left', padx=(12, 0))
        ttk.Button(buttons_frame, text='Ouvrir la liste enregistrée', command=self.open_saved_sounds_window).pack(side='left', padx=(12, 0))

    def update_selection(self, *_args) -> None:
        sound = self.lookup.get(self.selected_label.get())
        if sound is None:
            self.selected_event.set('')
            self.selected_path.set('')
            self.selected_comment.set('')
            return
        self.selected_event.set(sound['event'])
        self.selected_path.set(_resolve_sound_path(sound) or 'Aucun fichier associe')

        saved_sound = next((item for item in load_saved_sounds() if item['event'] == sound['event']), None)
        self.selected_comment.set(saved_sound.get('comment', '') if saved_sound else '')

    def on_play_selected(self) -> None:
        sound = self.lookup.get(self.selected_label.get())
        if sound is None:
            messagebox.showwarning('Lecture', 'Selectionne un son a jouer.')
            return
        self._play_sound_with_feedback(sound)

    def on_add_selected(self) -> None:
        sound = self.lookup.get(self.selected_label.get())
        if sound is None:
            messagebox.showwarning('Liste', 'Selectionne un son avant de l ajouter.')
            return

        saved_sounds = load_saved_sounds()
        if any(saved_sound['event'] == sound['event'] for saved_sound in saved_sounds):
            messagebox.showinfo('Liste', 'Ce son est deja present dans la liste enregistree.')
            self.open_saved_sounds_window()
            return

        saved_sounds.append(
            make_saved_sound_entry(
                {
                    **sound,
                    'comment': self.selected_comment.get().strip(),
                }
            )
        )
        save_saved_sounds(saved_sounds)
        self.open_saved_sounds_window()
        self.refresh_saved_sounds_window()

    def _play_sound_with_feedback(self, sound: dict[str, str]) -> None:
        try:
            play_sound(sound)
        except FileNotFoundError as exc:
            messagebox.showerror('Lecture impossible', str(exc))

    def open_saved_sounds_window(self) -> None:
        if self.saved_window is not None and self.saved_window.winfo_exists():
            self.saved_window.deiconify()
            self.saved_window.lift()
            self.refresh_saved_sounds_window()
            return

        self.saved_window = tk.Toplevel(self.root)
        self.saved_window.title('Liste des sons enregistres')
        self.saved_window.geometry('900x460')
        self.saved_window.configure(padx=16, pady=16)
        self.saved_window.protocol('WM_DELETE_WINDOW', self._close_saved_window)

        header = ttk.Label(
            self.saved_window,
            text='Ces sons seront reutilises plus tard pour associer des actions a Brapp.',
        )
        header.pack(anchor='w', pady=(0, 12))

        canvas = tk.Canvas(self.saved_window, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.saved_window, orient='vertical', command=canvas.yview)
        self.saved_list_frame = ttk.Frame(canvas)

        self.saved_list_frame.bind(
            '<Configure>',
            lambda _event: canvas.configure(scrollregion=canvas.bbox('all')),
        )

        canvas.create_window((0, 0), window=self.saved_list_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        self.refresh_saved_sounds_window()

    def refresh_saved_sounds_window(self) -> None:
        if self.saved_list_frame is None:
            return

        for widget in self.saved_list_frame.winfo_children():
            widget.destroy()

        saved_sounds = load_saved_sounds()
        if not saved_sounds:
            ttk.Label(self.saved_list_frame, text='Aucun son enregistre pour le moment.').pack(anchor='w')
            return

        for sound in saved_sounds:
            row = ttk.Frame(self.saved_list_frame, padding=(0, 8))
            row.pack(fill='x', expand=True)
            row.columnconfigure(0, weight=1)

            ttk.Label(row, text=sound['name']).grid(row=0, column=0, sticky='w')
            ttk.Label(row, text=_resolve_sound_path(sound) or 'Aucun fichier associe', wraplength=560).grid(
                row=1,
                column=0,
                sticky='w',
                pady=(4, 0),
            )
            comment_text = sound.get('comment', '').strip() or 'Aucun commentaire'
            ttk.Label(row, text=f'Commentaire : {comment_text}', wraplength=560).grid(
                row=2,
                column=0,
                sticky='w',
                pady=(4, 0),
            )
            ttk.Button(row, text='Jouer', command=lambda current_sound=sound: self._play_sound_with_feedback(current_sound)).grid(
                row=0,
                column=1,
                rowspan=3,
                padx=(16, 8),
            )
            ttk.Button(
                row,
                text='Modifier le commentaire',
                command=lambda event_name=sound['event']: self.edit_saved_sound_comment(event_name),
            ).grid(
                row=0,
                column=2,
                rowspan=3,
                padx=(0, 8),
            )
            ttk.Button(row, text='Supprimer', command=lambda event_name=sound['event']: self.delete_saved_sound(event_name)).grid(
                row=0,
                column=3,
                rowspan=3,
            )

            separator = ttk.Separator(self.saved_list_frame, orient='horizontal')
            separator.pack(fill='x', pady=(0, 4))

    def edit_saved_sound_comment(self, event_name: str) -> None:
        saved_sounds = load_saved_sounds()
        sound = next((item for item in saved_sounds if item['event'] == event_name), None)
        if sound is None:
            return

        new_comment = simpledialog.askstring(
            'Commentaire',
            f"Commentaire pour {sound['label']}",
            initialvalue=sound.get('comment', ''),
            parent=self.saved_window or self.root,
        )
        if new_comment is None:
            return

        sound['comment'] = new_comment.strip()
        save_saved_sounds(saved_sounds)
        if self.lookup.get(self.selected_label.get(), {}).get('event') == event_name:
            self.selected_comment.set(sound['comment'])
        self.refresh_saved_sounds_window()

    def delete_saved_sound(self, event_name: str) -> None:
        saved_sounds = load_saved_sounds()
        filtered_sounds = [sound for sound in saved_sounds if sound['event'] != event_name]
        save_saved_sounds(filtered_sounds)
        self.refresh_saved_sounds_window()

    def _close_saved_window(self) -> None:
        if self.saved_window is not None:
            self.saved_window.destroy()
        self.saved_window = None
        self.saved_list_frame = None

    def run(self) -> None:
        self.root.mainloop()


if __name__ == '__main__':
    SoundManagerApp().run()