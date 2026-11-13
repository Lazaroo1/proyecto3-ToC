"""Cinta de la Máquina de Turing."""

from typing import Dict, Iterable, List, Tuple

from .symbols import BLANK, Symbol
from .transition import Move


class Tape:
    """Cinta infinita en ambos sentidos con un único cabezal.

    Solo se guardan las celdas que NO son blank, en un diccionario
    ``posición -> símbolo``. Así la cinta puede crecer hacia la izquierda
    (posiciones negativas) o hacia la derecha sin desplazar listas, y
    cualquier celda que nunca se escribió vale blank.

    La cadena de entrada se coloca a partir de la posición 0 y el cabezal
    inicia sobre su primer símbolo.
    """

    def __init__(self, symbols: Iterable[Symbol] = (), head: int = 0):
        self._cells: Dict[int, str] = {}
        for position, symbol in enumerate(symbols):
            if symbol is not BLANK:
                self._cells[position] = symbol
        self.head = head

    def read(self) -> Symbol:
        """Símbolo que está bajo el cabezal."""
        return self._cells.get(self.head, BLANK)

    def write(self, symbol: Symbol) -> None:
        """Escribe un símbolo bajo el cabezal (escribir blank borra la celda)."""
        if symbol is BLANK:
            self._cells.pop(self.head, None)
        else:
            self._cells[self.head] = symbol

    def move(self, direction: Move) -> None:
        self.head += direction.offset

    def is_empty(self) -> bool:
        """True si toda la cinta es blank."""
        return not self._cells

    def bounds(self) -> Tuple[int, int]:
        """Rango [inicio, fin] que contiene todo lo que no es blank y al cabezal."""
        if not self._cells:
            return self.head, self.head
        return min(min(self._cells), self.head), max(max(self._cells), self.head)

    def segment(self, start: int, end: int) -> List[Symbol]:
        """Símbolos de las posiciones start..end (inclusive)."""
        return [self._cells.get(i, BLANK) for i in range(start, end + 1)]

    def split_at_head(self) -> Tuple[List[Symbol], List[Symbol]]:
        """Divide la parte visible en (izquierda del cabezal, desde el cabezal).

        La segunda lista siempre inicia con el símbolo bajo el cabezal.
        """
        start, end = self.bounds()
        return self.segment(start, self.head - 1), self.segment(self.head, end)

    def content(self) -> List[Symbol]:
        """Contenido entre el primer y el último símbolo que no es blank."""
        if not self._cells:
            return []
        return self.segment(min(self._cells), max(self._cells))

    def copy(self) -> "Tape":
        clone = Tape(head=self.head)
        clone._cells = dict(self._cells)
        return clone

    def __repr__(self) -> str:
        return f"Tape(content={self.content()!r}, head={self.head})"
