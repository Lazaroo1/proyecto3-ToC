"""Función de transición δ.

Siguiendo el formato del enunciado, el estado de la MT es un par
``[q, c]``: ``q`` es el estado de control y ``c`` el valor guardado en la
memoria caché (puede ser blank). Una transición tiene la forma

    δ([q, c], a) = ([p, d], b, M)

y se modela con dos objetos inmutables: los parámetros (lo que la MT
consulta) y la salida (lo que la MT hace). Como los parámetros son
inmutables y comparables, sirven de llave en un diccionario y buscar la
transición a aplicar en cada paso cuesta O(1).
"""

from dataclasses import dataclass
from enum import Enum

from .errors import MachineDefinitionError
from .symbols import BLANK_DISPLAY, Symbol, display_symbol


class Move(Enum):
    """Desplazamiento del cabezal sobre la cinta."""

    LEFT = "L"
    RIGHT = "R"
    STAY = "S"

    @property
    def offset(self) -> int:
        """Cuántas celdas se mueve el cabezal (-1, +1 o 0)."""
        return _OFFSETS[self]

    @classmethod
    def parse(cls, value) -> "Move":
        """Convierte el valor de ``tape_displacement`` (L, R o S) en un Move."""
        text = "" if value is None else str(value).strip().upper()
        for move in cls:
            if move.value == text:
                return move
        raise MachineDefinitionError(
            f"desplazamiento inválido '{value}': debe ser L, R o S"
        )


_OFFSETS = {Move.LEFT: -1, Move.RIGHT: 1, Move.STAY: 0}


@dataclass(frozen=True)
class TransitionParams:
    """Lado izquierdo de δ: ``([q, c], a)`` → bloque ``params`` del YAML."""

    state: str
    cache: Symbol
    read: Symbol


@dataclass(frozen=True)
class TransitionOutput:
    """Lado derecho de δ: ``([p, d], b, M)`` → bloque ``output`` del YAML."""

    state: str
    cache: Symbol
    write: Symbol
    move: Move


@dataclass(frozen=True)
class Transition:
    """Una regla completa de la función de transición."""

    params: TransitionParams
    output: TransitionOutput

    def format(self, blank: str = BLANK_DISPLAY) -> str:
        """Notación de clase: δ([q0, B], a) = ([q1, a], X, R)."""
        p, o = self.params, self.output
        sym = lambda s: display_symbol(s, blank)  # noqa: E731
        return (
            f"δ([{p.state}, {sym(p.cache)}], {sym(p.read)}) = "
            f"([{o.state}, {sym(o.cache)}], {sym(o.write)}, {o.move.value})"
        )

    def __str__(self) -> str:
        return self.format()
