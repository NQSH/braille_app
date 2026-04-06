from dataclasses import dataclass
from typing import Dict, FrozenSet

@dataclass(frozen=True)
class InputMode:
    name: str
    dot_key_map: Dict[str, int]
    validate_keys: FrozenSet[str]
    delete_keys: FrozenSet[str]
    delete_hold_key: str
    description: str


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
