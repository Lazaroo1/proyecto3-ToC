"""Presentación de resultados: encabezado de la MT, listado de IDs y resumen."""

from pathlib import Path
from typing import List, Sequence, Union

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


class Palette:
    """Colores ANSI; si está deshabilitada devuelve el texto sin cambios."""

    CODES = {
        "title": "1;36",
        "accept": "1;32",
        "reject": "1;31",
        "warn": "33",
        "state": "1;35",
        "dim": "2",
        "bold": "1",
    }

    def __init__(self, enabled: bool = False):
        self.enabled = enabled

    def paint(self, style: str, text: str) -> str:
        if not self.enabled or not text:
            return text
        return f"\033[{self.CODES[style]}m{text}\033[0m"


class Reporter:
    """Genera el texto que se muestra por cada máquina y cada cadena."""

    def __init__(self, color: bool = False, show_transitions: bool = True):
        self.palette = Palette(color)
        self.show_transitions = show_transitions

    def _paint(self, style: str, text: str) -> str:
        return self.palette.paint(style, text)

    # ------------------------------------------------------------ máquina
    def render_header(self, spec: MachineSpec) -> str:
        machine = spec.machine
        blank = machine.blank_display
        lines = [self._paint("title", "═" * WIDTH), self._paint("title", f" {spec.title}")]
        if machine.description:
            lines.append(f" {machine.description}")
        if spec.source:
            lines.append(self._paint("dim", f" Archivo: {spec.source}"))
        lines += [
            self._paint("title", "═" * WIDTH),
            f"  Q  = {format_set(machine.states)}",
            f"  Σ  = {format_set(machine.input_alphabet)}",
            f"  Γ  = {format_set(machine.tape_alphabet + [BLANK], blank)}",
            f"  q0 = {machine.initial_state}",
            f"  F  = {format_set(machine.final_states)}",
            f"  δ  : {len(machine.transitions)} transiciones",
        ]
        for warning in spec.warnings:
            lines.append(self._paint("warn", f"  ! Advertencia: {warning}"))
        return "\n".join(lines) + "\n\n"

    def render_error(self, path: Union[str, Path], error: Exception) -> str:
        return self._paint("reject", f"Error en '{path}': {error}") + "\n"

    # ------------------------------------------------------------- cadena
    def render_result(self, index: int, total: int, result: SimulationResult,
                      machine: TuringMachine) -> str:
        blank = machine.blank_display
        lines = [
            "─" * WIDTH,
            f" Cadena {index}/{total}: " + self._paint("bold", display_input(result.input_string)),
            "─" * WIDTH,
        ]
        lines += self._render_ids(result, blank)
        lines.append("")
        lines.append(f" Resultado: {self._outcome(result.outcome)}")
        lines.append(f"   {result.message}")
        if result.outcome is not Outcome.INVALID_INPUT:
            tape = join_symbols(result.final_tape, blank) if result.final_tape else "(solo blanks)"
            lines.append(" Cinta final: " + self._paint("bold", tape))
        return "\n".join(lines) + "\n\n"

    def _outcome(self, outcome: Outcome) -> str:
        return self._paint("accept" if outcome.accepted else "reject", OUTCOME_LABELS[outcome])

    # ------------------------------------------------------------ resumen
    def render_summary(self, spec: MachineSpec, results: Sequence[SimulationResult]) -> str:
        """Tabla con el veredicto de cada cadena de la máquina."""
        if not results:
            return ""
        blank = spec.machine.blank_display
        headers = ("#", "Cadena", "Resultado", "Pasos", "Cinta final")
        rows: List[tuple] = []
        for index, result in enumerate(results, start=1):
            simulated = result.outcome is not Outcome.INVALID_INPUT
            if not simulated:
                tape = "-"
            elif result.final_tape:
                tape = join_symbols(result.final_tape, blank)
            else:
                tape = "(solo blanks)"
            rows.append((
                str(index),
                display_input(result.input_string),
                OUTCOME_LABELS[result.outcome],
                str(result.steps) if simulated else "-",
                tape,
            ))
        widths = [max(len(h), *(len(row[k]) for row in rows)) for k, h in enumerate(headers)]

        def format_row(cells, outcome=None):
            padded = []
            for k, cell in enumerate(cells):
                text = cell.rjust(widths[k]) if k in (0, 3) else cell.ljust(widths[k])
                if k == 2 and outcome is not None:
                    text = self._paint("accept" if outcome.accepted else "reject", text)
                padded.append(text)
            return ("  " + "   ".join(padded)).rstrip()

        accepted = sum(1 for r in results if r.accepted)
        lines = [
            self._paint("title", f" Resumen — {spec.title}"),
            self._paint("bold", format_row(headers)),
            "  " + "-" * (sum(widths) + 3 * (len(widths) - 1)),
        ]
        lines += [format_row(row, r.outcome) for row, r in zip(rows, results)]
        lines.append(f"  Aceptadas: {accepted}/{len(results)}")
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
            # El ancho se calcula con el texto sin color para que se alinee igual.
            left, state, right = description.parts(blank)
            colored = " ".join(
                part for part in (left, self._paint("state", state), right) if part
            )
            line = f"  {prefix} {description.step:>{number_width}}   {colored}"
            if self.show_transitions and description.transition is not None:
                padding = " " * (id_width - len(text))
                line += padding + "   " + self._paint("dim", description.transition.format(blank))
            lines.append(line.rstrip())
        return lines
