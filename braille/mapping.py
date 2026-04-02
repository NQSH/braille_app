from typing import Dict, FrozenSet, Optional, Tuple

DotSet = FrozenSet[int]
NUMBER_SIGN = frozenset({3, 4, 5, 6})

LETTER_MAP: Dict[DotSet, str] = {
    frozenset({1}): 'a',
    frozenset({1, 2}): 'b',
    frozenset({1, 4}): 'c',
    frozenset({1, 4, 5}): 'd',
    frozenset({1, 5}): 'e',
    frozenset({1, 2, 4}): 'f',
    frozenset({1, 2, 4, 5}): 'g',
    frozenset({1, 2, 5}): 'h',
    frozenset({2, 4}): 'i',
    frozenset({2, 4, 5}): 'j',
    frozenset({1, 3}): 'k',
    frozenset({1, 2, 3}): 'l',
    frozenset({1, 3, 4}): 'm',
    frozenset({1, 3, 4, 5}): 'n',
    frozenset({1, 3, 5}): 'o',
    frozenset({1, 2, 3, 4}): 'p',
    frozenset({1, 2, 3, 4, 5}): 'q',
    frozenset({1, 2, 3, 5}): 'r',
    frozenset({2, 3, 4}): 's',
    frozenset({2, 3, 4, 5}): 't',
    frozenset({1, 3, 6}): 'u',
    frozenset({1, 2, 3, 6}): 'v',
    frozenset({1, 3, 4, 6}): 'x',
    frozenset({1, 3, 4, 5, 6}): 'y',
    frozenset({1, 3, 5, 6}): 'z',
    frozenset({1, 2, 3, 4, 6}): 'ç',
    frozenset({1, 2, 3, 4, 5, 6}): 'é',
    frozenset({1, 2, 3, 5, 6}): 'à',
    frozenset({2, 3, 4, 6}): 'è',
    frozenset({2, 3, 4, 5, 6}): 'ù',
    frozenset({1, 6}): 'â',
    frozenset({1, 2, 6}): 'ê',
    frozenset({1, 4, 6}): 'î',
    frozenset({1, 4, 5, 6}): 'ô',
    frozenset({1, 5, 6}): 'û',
    frozenset({1, 2, 4, 6}): 'ë',
    frozenset({1, 2, 4, 5, 6}): 'ï',
    frozenset({1, 2, 5, 6}): 'ü',
    frozenset({2, 4, 6}): 'œ',
    frozenset({2, 4, 5, 6}): 'w',
}

PUNCTUATION_MAP: Dict[DotSet, str] = {
    frozenset({2}): ',',
    frozenset({2, 3}): ';',
    frozenset({2, 5}): ':',
    frozenset({2, 5, 6}): '.',
    frozenset({2, 3, 6}): '?',
    frozenset({2, 3, 5}): '!',
    frozenset({3}): "'",
    frozenset({1, 6}): '(',
    frozenset({3, 4, 5, 6}): ')',
}

DIGIT_MAP: Dict[DotSet, str] = {
    frozenset({1}): '1',
    frozenset({1, 2}): '2',
    frozenset({1, 4}): '3',
    frozenset({1, 4, 5}): '4',
    frozenset({1, 5}): '5',
    frozenset({1, 2, 4}): '6',
    frozenset({1, 2, 4, 5}): '7',
    frozenset({1, 2, 5}): '8',
    frozenset({2, 4}): '9',
    frozenset({2, 4, 5}): '0',
}


EXTENDED_MAP: Dict[DotSet, str] = {**LETTER_MAP, **DIGIT_MAP, **PUNCTUATION_MAP}


class BrailleTranslator:
    def __init__(self) -> None:
        self.number_mode = False

    def reset(self) -> None:
        self.number_mode = False

    def translate(self, dots: DotSet) -> Tuple[Optional[str], bool]:
        if dots == NUMBER_SIGN:
            self.number_mode = True
            return None, True

        if self.number_mode:
            result = DIGIT_MAP.get(dots)
            self.number_mode = False
            return (result if result is not None else '?'), False

        return (EXTENDED_MAP.get(dots, '?'), False)
