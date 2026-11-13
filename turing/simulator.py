"""Simulación de la MT usando la función de transición δ."""

from dataclasses import dataclass
from typing import Iterable, Optional

from .instantaneous import InstantaneousDescription
from .machine import TuringMachine
from .symbols import BLANK, Symbol
from .tape import Tape
from .transition import Transition


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

    def __init__(self, machine: TuringMachine):
        self.machine = machine

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
