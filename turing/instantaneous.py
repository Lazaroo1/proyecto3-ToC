"""Descripciones instantáneas (IDs) de la MT."""

from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

from .symbols import BLANK_DISPLAY, Symbol, display_symbol
from .tape import Tape
from .transition import Transition


def join_symbols(symbols: Sequence[Symbol], blank: str = BLANK_DISPLAY) -> str:
    """Une símbolos para imprimirlos.

    Si todos son de un carácter se escriben pegados (``aab#aab``); si hay
    símbolos más largos se separan con espacios para que no se confundan.
    """
    texts = [display_symbol(s, blank) for s in symbols]
    joiner = "" if all(len(t) == 1 for t in texts) else " "
    return joiner.join(texts)


@dataclass(frozen=True)
class InstantaneousDescription:
    """ID de la forma  α [q, c] β.

    * ``α`` (left): símbolos a la izquierda del cabezal.
    * ``[q, c]``: estado de control y valor de la caché.
    * ``β`` (right): inicia con el símbolo que está bajo el cabezal.

    Igual que en clase, se omiten los blanks de los extremos salvo el que
    esté bajo el cabezal. ``transition`` es la regla de δ que se aplicó para
    llegar a esta ID (None en la ID inicial).
    """

    step: int
    state: str
    cache: Symbol
    left: Tuple[Symbol, ...]
    right: Tuple[Symbol, ...]
    transition: Optional[Transition] = None

    @classmethod
    def capture(cls, step: int, state: str, cache: Symbol, tape: Tape,
                transition: Optional[Transition] = None) -> "InstantaneousDescription":
        left, right = tape.split_at_head()
        return cls(step, state, cache, tuple(left), tuple(right), transition)

    @property
    def head_symbol(self) -> Symbol:
        return self.right[0]

    def parts(self, blank: str = BLANK_DISPLAY) -> Tuple[str, str, str]:
        """(α, [q, c], β) ya formateados, para poder darles estilo por separado."""
        everything = self.left + self.right
        texts = [display_symbol(s, blank) for s in everything]
        joiner = "" if all(len(t) == 1 for t in texts) else " "
        left = joiner.join(texts[: len(self.left)])
        right = joiner.join(texts[len(self.left):])
        state = f"[{self.state}, {display_symbol(self.cache, blank)}]"
        return left, state, right

    def format(self, blank: str = BLANK_DISPLAY) -> str:
        """Ejemplo: ``Xab [q1, a] #aab``."""
        return " ".join(part for part in self.parts(blank) if part)

    def __str__(self) -> str:
        return self.format()
