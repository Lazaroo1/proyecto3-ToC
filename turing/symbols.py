"""Símbolos de la cinta y manejo del blank.

En el archivo YAML el blank se escribe como una entrada vacía (null/None).
Internamente se representa con ``None`` para que nunca choque con un
símbolo real de los alfabetos.
"""

from typing import Iterable, Optional

#: Un símbolo es un texto (``"a"``, ``"#"``, ``"X"``...) o el blank (``None``).
Symbol = Optional[str]

BLANK: Symbol = None

#: Cómo se muestra el blank en las IDs y transiciones (igual que en clase: B).
BLANK_DISPLAY = "B"

#: Representación alterna del blank cuando "B" ya es un símbolo de Γ.
ALT_BLANK_DISPLAY = "□"

_BLANK_LITERALS = frozenset({"", "~", "null", "Null", "NULL", "none", "None", "NONE"})


def normalize_symbol(value) -> Symbol:
    """Convierte un valor leído del YAML en un símbolo de la máquina.

    Las entradas vacías, ``null``, ``~`` o ``None`` se interpretan como blank.
    Cualquier otro valor se convierte a texto (sin espacios a los lados).
    """
    if value is None:
        return BLANK
    text = str(value).strip()
    if text in _BLANK_LITERALS:
        return BLANK
    return text


def is_blank(symbol: Symbol) -> bool:
    return symbol is BLANK


def display_symbol(symbol: Symbol, blank: str = BLANK_DISPLAY) -> str:
    """Texto con el que se imprime un símbolo."""
    return blank if symbol is BLANK else symbol


def choose_blank_display(alphabet: Iterable[Symbol]) -> str:
    """Elige cómo mostrar el blank sin que se confunda con otro símbolo."""
    return ALT_BLANK_DISPLAY if BLANK_DISPLAY in set(alphabet) else BLANK_DISPLAY


def format_set(symbols: Iterable[Symbol], blank: str = BLANK_DISPLAY) -> str:
    """Formatea una colección de símbolos o estados como conjunto: {a, b, B}."""
    return "{" + ", ".join(display_symbol(s, blank) for s in symbols) + "}"
