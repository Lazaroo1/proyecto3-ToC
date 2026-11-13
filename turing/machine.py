"""Modelo de la Máquina de Turing de una cinta.

M = (Q, Σ, Γ, δ, q0, B, F), donde cada estado es un par [q, c] con c el
valor de la memoria caché. La función δ se guarda en un diccionario cuya
llave son los parámetros ([q, c], a), de modo que en cada paso de la
simulación encontrar la transición a aplicar es una sola búsqueda.
"""

from typing import Dict, Iterable, List, Optional

from .symbols import BLANK, Symbol, choose_blank_display, display_symbol
from .transition import Transition, TransitionParams


def _unique(items: Iterable) -> List:
    """Quita repetidos conservando el orden en que aparecen."""
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


class TuringMachine:
    """Descripción formal de una MT de una cinta."""

    def __init__(
        self,
        states: Iterable[str],
        initial_state: str,
        final_states: Iterable[str],
        input_alphabet: Iterable[Symbol],
        tape_alphabet: Iterable[Symbol],
        transitions: Iterable[Transition] = (),
        name: Optional[str] = None,
        description: Optional[str] = None,
    ):
        self.name = name
        self.description = description
        self.states: List[str] = _unique(states)
        self.initial_state = initial_state
        self.final_states: List[str] = _unique(final_states)
        self.input_alphabet: List[Symbol] = _unique(input_alphabet)
        self.tape_alphabet: List[Symbol] = _unique(
            s for s in tape_alphabet if s is not BLANK
        )
        self.blank_display = choose_blank_display(self.tape_alphabet)

        self.delta: Dict[TransitionParams, Transition] = {}
        for transition in transitions:
            self.add_transition(transition)

    # ------------------------------------------------------------------ δ
    def add_transition(self, transition: Transition) -> None:
        self.delta[transition.params] = transition

    def transition_for(self, state: str, cache: Symbol, symbol: Symbol) -> Optional[Transition]:
        """δ([state, cache], symbol) o None si no está definida."""
        return self.delta.get(TransitionParams(state, cache, symbol))

    @property
    def transitions(self) -> List[Transition]:
        return list(self.delta.values())

    # ------------------------------------------------------------ consultas
    def is_final(self, state: str) -> bool:
        return state in self.final_states

    def format_symbol(self, symbol: Symbol) -> str:
        return display_symbol(symbol, self.blank_display)
