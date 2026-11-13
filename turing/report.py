"""Presentación de resultados: encabezado de la MT y listado de IDs."""

from typing import Union
from pathlib import Path

from .instantaneous import join_symbols
from .loader import MachineSpec
from .machine import TuringMachine
from .simulator import Outcome, SimulationResult
from .symbols import BLANK, format_set

WIDTH = 78
TURNSTILE = "⊢"

OUTCOME_LABELS = {
    Outcome.ACCEPTED: "ACEPTADA",
    Outcome.REJECTED: "RECHAZADA",
    Outcome.STEP_LIMIT: "RECHAZADA (límite de pasos)",
    Outcome.INVALID_INPUT: "RECHAZADA (entrada inválida)",
}


def display_input(text: str) -> str:
    return text if text else "ε"


class Reporter:
    """Genera el texto que se muestra por cada máquina y cada cadena."""

    def __init__(self, show_transitions: bool = True):
        self.show_transitions = show_transitions

    # ------------------------------------------------------------ máquina
    def render_header(self, spec: MachineSpec) -> str:
        machine = spec.machine
        blank = machine.blank_display
        lines = ["═" * WIDTH, f" {spec.title}"]
        if machine.description:
            lines.append(f" {machine.description}")
        if spec.source:
            lines.append(f" Archivo: {spec.source}")
        lines += [
            "═" * WIDTH,
            f"  Q  = {format_set(machine.states)}",
            f"  Σ  = {format_set(machine.input_alphabet)}",
            f"  Γ  = {format_set(machine.tape_alphabet + [BLANK], blank)}",
            f"  q0 = {machine.initial_state}",
            f"  F  = {format_set(machine.final_states)}",
            f"  δ  : {len(machine.transitions)} transiciones",
        ]
        for warning in spec.warnings:
            lines.append(f"  ! Advertencia: {warning}")
        return "\n".join(lines) + "\n\n"

    def render_error(self, path: Union[str, Path], error: Exception) -> str:
        return f"Error en '{path}': {error}\n"

    # ------------------------------------------------------------- cadena
    def render_result(self, index: int, total: int, result: SimulationResult,
                      machine: TuringMachine) -> str:
        blank = machine.blank_display
        lines = [
            "─" * WIDTH,
            f" Cadena {index}/{total}: {display_input(result.input_string)}",
            "─" * WIDTH,
        ]
        lines += self._render_ids(result, blank)
        lines.append("")
        lines.append(f" Resultado: {OUTCOME_LABELS[result.outcome]}")
        lines.append(f"   {result.message}")
        if result.outcome is not Outcome.INVALID_INPUT:
            tape = join_symbols(result.final_tape, blank) if result.final_tape else "(solo blanks)"
            lines.append(f" Cinta final: {tape}")
        return "\n".join(lines) + "\n\n"

    def _render_ids(self, result: SimulationResult, blank: str) -> list:
        if not result.ids:
            return []
        number_width = len(str(result.ids[-1].step))
        texts = [i.format(blank) for i in result.ids]
        id_width = max(len(t) for t in texts)
        lines = []
        for description, text in zip(result.ids, texts):
            prefix = TURNSTILE if description.step else " "
            line = f"  {prefix} {description.step:>{number_width}}   {text}"
            if self.show_transitions and description.transition is not None:
                padding = " " * (id_width - len(text))
                line += f"{padding}   {description.transition.format(blank)}"
            lines.append(line.rstrip())
        return lines
