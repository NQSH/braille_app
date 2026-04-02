import tkinter as tk


def create_rounded_label(parent, bg, fg, radius, width=100, height=50, text='', font=('Arial', 12), pixels_per_char=10):
    if text:
        width = len(text) * pixels_per_char + 20
        if height == 50:
            height = font[1] + 10 if len(font) > 1 else 30

    canvas = tk.Canvas(parent, width=width, height=height, bg=parent['bg'], highlightthickness=0)

    def round_rectangle(x1, y1, x2, y2, radius=radius):
        points = [x1 + radius, y1, x2 - radius, y1, x2, y1, x2, y1 + radius, x2, y2 - radius, x2, y2, x2 - radius, y2, x1 + radius, y2, x1, y2, x1, y2 - radius, x1, y1 + radius, x1, y1]
        return canvas.create_polygon(points, fill=bg, outline='', smooth=True)

    round_rectangle(2, 2, width - 2, height - 2, radius)
    text_id = canvas.create_text(width / 2, height / 2, text=text, font=font, fill=fg)
    return canvas, text_id


def create_braille_canvas(parent, dots: frozenset[int], size=20):
    canvas = tk.Canvas(parent, width=2 * size, height=3 * size, bg='white', highlightthickness=0)
    positions = {
        1: (0, 0),
        2: (0, 1),
        3: (0, 2),
        4: (1, 0),
        5: (1, 1),
        6: (1, 2),
    }
    for i in range(1, 7):
        col, row = positions[i]
        x = col * size + size // 2
        y = row * size + size // 2
        color = 'black' if i in dots else 'white'
        canvas.create_oval(x - size // 4, y - size // 4, x + size // 4, y + size // 4, fill=color, outline='black')
    return canvas


def create_braille_grid(parent, mapping: dict, breaks: list = None, max_cols=10):
    if breaks is None:
        breaks = []
    current_row_frame = None
    col = 0
    for dots, char in mapping.items():
        if char in breaks or col == 0:
            current_row_frame = tk.Frame(parent, bg=parent['bg'])
            current_row_frame.pack(pady=2)
            col = 0

        pair_frame = tk.Frame(current_row_frame, bg=parent['bg'])
        pair_frame.pack(side='left', padx=5)
        braille_canvas = create_braille_canvas(pair_frame, dots, size=15)
        braille_canvas.pack()
        tk.Label(pair_frame, text=char.upper() if isinstance(char, str) and char.isalpha() else char, font=('Arial', 10, 'bold'), fg='white', bg=parent['bg']).pack()
        col += 1
        if col >= max_cols:
            col = 0
