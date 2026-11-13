"""Parsing de las cadenas de entrada que se colocan en la cinta.

Una cadena como ``aab#aab`` se divide en símbolos del alfabeto de entrada
Σ antes de escribirse en la cinta. Reglas:

* Si la cadena tiene espacios, cada palabra es un símbolo. Así se pueden
  usar símbolos de más de un carácter: ``"q1 q2 #"``.
* Si no tiene espacios, se busca una forma de partirla en símbolos de Σ
  prefiriendo los símbolos más largos. Con alfabetos de un carácter esto
  equivale a separarla carácter por carácter.
* Si algún fragmento no pertenece a Σ se lanza TapeInputError: la cadena
  no puede ser procesada por la MT.
"""

from typing import Iterable, List, Optional, Sequence

from .errors import TapeInputError
from .symbols import BLANK, Symbol, format_set


def parse_input(text: str, input_alphabet: Iterable[Symbol],
                tape_alphabet: Iterable[Symbol] = ()) -> List[str]:
    """Convierte una cadena de entrada en la lista de símbolos de la cinta."""
    sigma = [s for s in input_alphabet if s is not BLANK]
    gamma = set(tape_alphabet)
    text = text.strip()
    if not text:
        return []  # cadena vacía ε: la cinta queda toda en blank

    if any(ch.isspace() for ch in text):
        tokens = text.split()
        for position, token in enumerate(tokens, start=1):
            if token not in sigma:
                raise TapeInputError(_unknown(token, f"símbolo #{position}", sigma, gamma))
        return tokens

    tokens = _segment(text, sigma)
    if tokens is None:
        position = _first_unmatched(text, sigma)
        raise TapeInputError(_unknown(text[position], f"posición {position + 1}", sigma, gamma))
    return tokens


def _segment(text: str, sigma: Sequence[str]) -> Optional[List[str]]:
    """Parte ``text`` en símbolos de Σ (programación dinámica de derecha a izquierda).

    ``rest[i]`` guarda una partición válida de ``text[i:]`` o None si no
    existe. Se prueban primero los símbolos más largos.
    """
    by_length = sorted(sigma, key=len, reverse=True)
    n = len(text)
    rest: List[Optional[List[str]]] = [None] * (n + 1)
    rest[n] = []
    for i in range(n - 1, -1, -1):
        for symbol in by_length:
            j = i + len(symbol)
            if text.startswith(symbol, i) and rest[j] is not None:
                rest[i] = [symbol] + rest[j]
                break
    return rest[0]


def _first_unmatched(text: str, sigma: Sequence[str]) -> int:
    """Primera posición donde ningún símbolo de Σ encaja (para el mensaje de error)."""
    i = 0
    while i < len(text):
        matches = [s for s in sigma if text.startswith(s, i)]
        if not matches:
            return i
        i += len(max(matches, key=len))
    return 0


def _unknown(fragment: str, where: str, sigma: Sequence[str], gamma: set) -> str:
    detail = "es un símbolo de la cinta (Γ) pero no de entrada" if fragment in gamma else "no pertenece al alfabeto"
    return (
        f"'{fragment}' ({where}) {detail}: Σ = {format_set(sigma)}"
    )
