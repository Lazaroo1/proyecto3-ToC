"""Simulación de la MT usando la función de transición δ.

Algoritmo (MT determinista que se detiene al aceptar):

1. Se parsea la cadena de entrada en símbolos de Σ y se escribe en la
   cinta; la configuración inicial es [q0, B] con el cabezal en el primer
   símbolo.
2. Mientras el estado actual no sea final, se busca δ([q, c], a) con a el
   símbolo bajo el cabezal y se aplica, guardando la nueva ID.
3. Si se llega a un estado final la cadena es ACEPTADA. Si no existe una
   transición para la configuración actual, la MT se detiene sin aceptar y
   la cadena es RECHAZADA.
4. Como una MT puede no detenerse nunca, se fija un límite de pasos. Si se
   alcanza sin llegar a un estado final, la cadena se reporta como
   rechazada por límite de pasos.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, List, Optional

from .errors import TapeInputError
from .input_parser import parse_input
from .instantaneous import InstantaneousDescription
from .machine import TuringMachine
from .symbols import BLANK, Symbol
from .tape import Tape
from .transition import Transition


class Outcome(Enum):
    """Cómo terminó la simulación de una cadena."""

    ACCEPTED = "aceptada"
    REJECTED = "rechazada"
    STEP_LIMIT = "límite de pasos"
    INVALID_INPUT = "entrada inválida"

    @property
    def accepted(self) -> bool:
        return self is Outcome.ACCEPTED


@dataclass
class SimulationResult:
    """Resultado de simular una cadena: todas las IDs y el veredicto."""

    input_string: str
    outcome: Outcome
    message: str
    ids: List[InstantaneousDescription] = field(default_factory=list)
    final_tape: List[Symbol] = field(default_factory=list)

    @property
    def accepted(self) -> bool:
        return self.outcome.accepted

    @property
    def steps(self) -> int:
        """Cantidad de transiciones aplicadas."""
        return max(len(self.ids) - 1, 0)

    @property
    def final_id(self) -> Optional[InstantaneousDescription]:
        return self.ids[-1] if self.ids else None


@dataclass
class Configuration:
    """Estado completo de la MT en un instante: [q, c], la cinta y el cabezal."""

    state: str
    cache: Symbol
    tape: Tape
    steps: int = 0

    def snapshot(self, transition: Optional[Transition] = None) -> InstantaneousDescription:
        """ID que corresponde a esta configuración."""
        return InstantaneousDescription.capture(
            self.steps, self.state, self.cache, self.tape, transition
        )


class Simulator:
    """Ejecuta una MT determinista de una cinta."""

    DEFAULT_MAX_STEPS = 10_000

    def __init__(self, machine: TuringMachine, max_steps: int = DEFAULT_MAX_STEPS):
        if max_steps < 1:
            raise ValueError("max_steps debe ser al menos 1")
        self.machine = machine
        self.max_steps = max_steps

    def initial_configuration(self, symbols: Iterable[Symbol]) -> Configuration:
        """[q0, B] con la entrada en la cinta y el cabezal en su primer símbolo."""
        return Configuration(self.machine.initial_state, BLANK, Tape(symbols))

    def step(self, config: Configuration) -> Optional[Transition]:
        """Aplica δ una vez sobre ``config``.

        Busca δ([q, c], a) con a el símbolo bajo el cabezal. Si existe,
        escribe el símbolo, mueve el cabezal y cambia a [p, d]; devuelve la
        transición usada. Si no existe, la MT se detiene y devuelve None.
        """
        transition = self.machine.transition_for(config.state, config.cache, config.tape.read())
        if transition is None:
            return None
        output = transition.output
        config.tape.write(output.write)
        config.tape.move(output.move)
        config.state = output.state
        config.cache = output.cache
        config.steps += 1
        return transition

    def run(self, input_string: str) -> SimulationResult:
        """Simula la cadena completa y devuelve todas sus IDs."""
        machine = self.machine
        try:
            symbols = parse_input(input_string, machine.input_alphabet, machine.tape_alphabet)
        except TapeInputError as error:
            return SimulationResult(input_string, Outcome.INVALID_INPUT, str(error))

        config = self.initial_configuration(symbols)
        ids = [config.snapshot()]
        while True:
            if machine.is_final(config.state):
                return self._finish(
                    input_string, Outcome.ACCEPTED, ids, config,
                    f"la MT se detuvo en el estado de aceptación {config.state} "
                    f"después de {_steps(config.steps)}",
                )
            if config.steps >= self.max_steps:
                return self._finish(
                    input_string, Outcome.STEP_LIMIT, ids, config,
                    f"se alcanzó el límite de {_steps(self.max_steps)} sin llegar a un "
                    "estado de aceptación (posible ciclo infinito)",
                )
            state, cache, read = config.state, config.cache, config.tape.read()
            transition = self.step(config)
            if transition is None:
                fmt = machine.format_symbol
                return self._finish(
                    input_string, Outcome.REJECTED, ids, config,
                    f"no existe δ([{state}, {fmt(cache)}], {fmt(read)}) y {state} "
                    f"no es un estado de aceptación; la MT se detuvo después de "
                    f"{_steps(config.steps)}",
                )
            ids.append(config.snapshot(transition))

    @staticmethod
    def _finish(input_string: str, outcome: Outcome, ids: List[InstantaneousDescription],
                config: Configuration, message: str) -> SimulationResult:
        return SimulationResult(input_string, outcome, message, ids, config.tape.content())


def _steps(count: int) -> str:
    return "1 paso" if count == 1 else f"{count} pasos"
