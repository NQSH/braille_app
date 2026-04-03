from dataclasses import dataclass
from typing import Dict, FrozenSet, Sequence

@dataclass(frozen=True)
class InputMode:
    name: str
    dot_key_map: Dict[str, int]
    validate_keys: FrozenSet[str]
    delete_keys: FrozenSet[str]
    delete_hold_key: str
    description: str


NUMPAD_MODE = InputMode(
    name='numpad',
    dot_key_map={
        '7': 1,
        '4': 2,
        '1': 3,
        '8': 4,
        '5': 5,
        '2': 6,
    },
    validate_keys=frozenset({'0'}),
    delete_keys=frozenset({'BackSpace', 'period', 'KP_Decimal', 'Delete'}),
    delete_hold_key='BackSpace',
    description='Saisie braille sur pavé numérique',
)

PERKINS_MODE = InputMode(
    name='perkins',
    dot_key_map={
        's': 3,
        'd': 2,
        'f': 1,
        'j': 4,
        'k': 5,
        'l': 6,
    },
    validate_keys=frozenset({'space'}),
    delete_keys=frozenset({'m'}),
    delete_hold_key='m',
    description='Saisie braille séquentielle façon Perkins',
)

AVAILABLE_MODES: Sequence[InputMode] = [NUMPAD_MODE, PERKINS_MODE]
