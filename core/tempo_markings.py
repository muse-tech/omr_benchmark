import re
from typing import Tuple, Optional

TEMPO_MARKINGS = [
    "Grave",
    "Largo",
    "Larghetto",
    "Lento",
    "Adagio",
    "Adagietto",
    "Andante",
    "Andantino",
    "Moderato",
    "Allegretto",
    "Allegro",
    "Vivace",
    "Vivacissimo",
    "Presto",
    "Prestissimo",
]

TEMPO_MARKINGS_NORMALIZED = {marking.lower().strip(): marking for marking in TEMPO_MARKINGS}

def normalize_tempo_marking(tempo: str) -> str:
    if not tempo:
        return tempo
    normalized = tempo.strip()
    if normalized in TEMPO_MARKINGS:
        return normalized
    lower_normalized = normalized.lower()
    if lower_normalized in TEMPO_MARKINGS_NORMALIZED:
        return TEMPO_MARKINGS_NORMALIZED[lower_normalized]
    return tempo

def is_valid_tempo_marking(tempo: str) -> bool:
    if not tempo:
        return False
    normalized = tempo.strip().lower()
    return normalized in TEMPO_MARKINGS_NORMALIZED


def contains_tempo_marking(text: str) -> Tuple[bool, Optional[str]]:
    if not text:
        return False, None
    text_normalized = text.strip()

    if is_valid_tempo_marking(text_normalized):
        return True, normalize_tempo_marking(text_normalized)
    sorted_markings = sorted(TEMPO_MARKINGS, key=len, reverse=True)

    text_lower = text_normalized.lower()
    for marking in sorted_markings:
        marking_lower = marking.lower()
        if text_lower.startswith(marking_lower):
            remaining = text_normalized[len(marking):].strip()
            if not remaining or remaining[0] in ' .,;:!?':
                return True, marking

    for marking in sorted_markings:
        marking_lower = marking.lower()
        pattern = r'\b' + re.escape(marking_lower) + r'\b'
        if re.search(pattern, text_lower):
            return True, marking
    return False, None
