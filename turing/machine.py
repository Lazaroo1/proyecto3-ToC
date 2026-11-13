"""Modelo de la Máquina de Turing de una cinta.

M = (Q, Σ, Γ, δ, q0, B, F), donde cada estado es un par [q, c] con c el
valor de la memoria caché. La función δ se guarda en un diccionario cuya
llave son los parámetros ([q, c], a), de modo que en cada paso de la
simulación encontrar la transición a aplicar es una sola búsqueda.
"""

from typing import Dict, Iterable, List, Optional

from .errors import MachineDefinitionError
from .symbols import BLANK, Symbol, choose_blank_display, display_symbol, format_set
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
    """Descripción formal de una MT de una cinta.

    Al construirse valida la definición y lanza MachineDefinitionError si
    algo es inconsistente (estados que no existen, símbolos fuera de Γ,
    transiciones en conflicto...). Los problemas que no impiden simular se
    guardan en ``warnings``.
    """

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
        self.warnings: List[str] = []
        self._validate_definition()
        self.blank_display = choose_blank_display(self.tape_alphabet)

        self.delta: Dict[TransitionParams, Transition] = {}
        for index, transition in enumerate(transitions, start=1):
            self.add_transition(transition, index)

    # ----------------------------------------------------------- validación
    def _validate_definition(self) -> None:
        if not self.states:
            raise MachineDefinitionError("la lista de estados (q_list) está vacía")
        if self.initial_state not in self.states:
            raise MachineDefinitionError(
                f"el estado inicial '{self.initial_state}' no está en q_list"
            )
        if not self.final_states:
            raise MachineDefinitionError("debe indicar al menos un estado final")
        for state in self.final_states:
            if state not in self.states:
                raise MachineDefinitionError(f"el estado final '{state}' no está en q_list")

        if not self.input_alphabet:
            raise MachineDefinitionError("el alfabeto de entrada (alphabet) está vacío")
        if BLANK in self.input_alphabet:
            raise MachineDefinitionError(
                "el blank no puede pertenecer al alfabeto de entrada Σ"
            )

        # Σ ⊆ Γ: si a tape_alphabet le faltan símbolos de alphabet se agregan.
        missing = [s for s in self.input_alphabet if s not in self.tape_alphabet]
        if missing:
            self.tape_alphabet = missing + self.tape_alphabet
            self.warnings.append(
                f"tape_alphabet no incluía {format_set(missing)} de alphabet; "
                "se agregaron porque Σ ⊆ Γ"
            )

    def _check_symbol(self, symbol: Symbol, field: str, where: str) -> None:
        if symbol is not BLANK and symbol not in self.tape_alphabet:
            raise MachineDefinitionError(
                f"{where}{field} = '{symbol}' no pertenece al alfabeto de la cinta Γ = "
                f"{format_set(self.tape_alphabet + [BLANK], self.blank_display)}"
            )

    # ------------------------------------------------------------------ δ
    def add_transition(self, transition: Transition, index: Optional[int] = None) -> None:
        """Agrega una regla a δ validando estados, símbolos y determinismo."""
        where = f"delta[{index}]: " if index is not None else ""
        params, output = transition.params, transition.output

        for field, state in (("params.initial_state", params.state),
                             ("output.final_state", output.state)):
            if state not in self.states:
                raise MachineDefinitionError(
                    f"{where}{field} = '{state}' no está en q_list"
                )
        self._check_symbol(params.read, "params.tape_input", where)
        self._check_symbol(params.cache, "params.mem_cache_value", where)
        self._check_symbol(output.write, "output.tape_output", where)
        self._check_symbol(output.cache, "output.mem_cache_value", where)

        existing = self.delta.get(params)
        if existing is not None:
            if existing.output == output:
                self.warnings.append(
                    f"{where}transición repetida {transition.format(self.blank_display)}"
                )
                return
            raise MachineDefinitionError(
                f"{where}la MT no es determinista: ya existe "
                f"{existing.format(self.blank_display)} y se intenta agregar "
                f"{transition.format(self.blank_display)}"
            )

        if params.state in self.final_states:
            self.warnings.append(
                f"{where}{transition.format(self.blank_display)} sale de un estado "
                "final; nunca se usa porque la MT se detiene al aceptar"
            )
        self.delta[params] = transition

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
