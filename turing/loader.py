"""Parsing del archivo YAML con la descripción formal de la MT.

Formato esperado (el del enunciado)::

    q_states:
      q_list: [...]
      initial: '0'
      final: '5'
    alphabet: [...]
    tape_alphabet: [...]      # el blank se escribe como una entrada vacía
    delta:
    - params:
        initial_state: ...
        mem_cache_value: ...  # vacío = blank
        tape_input: ...
      output:
        final_state: ...
        mem_cache_value: ...
        tape_output: ...
        tape_displacement: L | R | S
    simulation_strings: [...]

Opcionalmente se aceptan las llaves ``name`` y ``description`` para
identificar la máquina en la salida.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Mapping, Optional, Union

import yaml

from .errors import MachineDefinitionError
from .machine import TuringMachine
from .symbols import normalize_symbol
from .transition import Move, Transition, TransitionOutput, TransitionParams

KNOWN_KEYS = (
    "q_states",
    "alphabet",
    "tape_alphabet",
    "delta",
    "simulation_strings",
    "name",
    "description",
)


@dataclass
class MachineSpec:
    """Resultado de leer un archivo: la MT y las cadenas a simular."""

    machine: TuringMachine
    simulation_strings: List[str]
    source: Optional[Path] = None
    warnings: List[str] = field(default_factory=list)

    @property
    def title(self) -> str:
        if self.machine.name:
            return self.machine.name
        return self.source.name if self.source else "Máquina de Turing"


def load_machine_file(path: Union[str, Path]) -> MachineSpec:
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise MachineDefinitionError(
            f"no se pudo leer '{path}': {error.strerror or error}"
        ) from error
    spec = load_machine_text(text)
    spec.source = path
    return spec


def load_machine_text(text: str) -> MachineSpec:
    try:
        # BaseLoader deja todos los escalares como texto. Con safe_load, YAML
        # convierte valores como 0101 (octal → 65), 10 (int) o yes/no (bool),
        # lo que rompe estados como '0' o cadenas binarias como 0101. Las
        # entradas vacías quedan como '' y normalize_symbol las toma como blank.
        document = yaml.load(text, Loader=yaml.BaseLoader)
    except yaml.YAMLError as error:
        raise MachineDefinitionError(f"el archivo YAML no es válido:\n{error}") from error
    return parse_document(document)


def parse_document(document: Any) -> MachineSpec:
    """Construye la MT a partir del documento YAML ya cargado."""
    if not isinstance(document, Mapping):
        raise MachineDefinitionError(
            "el YAML debe ser un objeto con las llaves q_states, alphabet, "
            "tape_alphabet y delta"
        )
    warnings = [
        f"llave desconocida '{key}' ignorada" for key in document if key not in KNOWN_KEYS
    ]

    q_states = _require(document, "q_states", Mapping)
    states = [_text(q, "q_states.q_list") for q in _require(q_states, "q_list", list, "q_states.")]
    initial = _text(_require(q_states, "initial", None, "q_states."), "q_states.initial")
    final = _require(q_states, "final", None, "q_states.")
    finals = final if isinstance(final, list) else [final]
    final_states = [_text(q, "q_states.final") for q in finals]

    alphabet = [normalize_symbol(s) for s in _require(document, "alphabet", list)]
    tape_alphabet = [normalize_symbol(s) for s in _require(document, "tape_alphabet", list)]

    transitions = [
        _parse_transition(entry, index)
        for index, entry in enumerate(_require(document, "delta", list), start=1)
    ]

    machine = TuringMachine(
        states=states,
        initial_state=initial,
        final_states=final_states,
        input_alphabet=alphabet,
        tape_alphabet=tape_alphabet,
        transitions=transitions,
        name=_optional_text(document.get("name")),
        description=_optional_text(document.get("description")),
    )
    strings = _parse_simulation_strings(document, warnings)
    return MachineSpec(machine, strings, warnings=warnings + machine.warnings)


def _parse_transition(entry: Any, index: int) -> Transition:
    where = f"delta[{index}]"
    if not isinstance(entry, Mapping):
        raise MachineDefinitionError(f"{where} debe tener los bloques params y output")
    params = _require(entry, "params", Mapping, f"{where}.")
    output = _require(entry, "output", Mapping, f"{where}.")
    try:
        return Transition(
            TransitionParams(
                state=_text(_require(params, "initial_state", None), "initial_state"),
                cache=normalize_symbol(params.get("mem_cache_value")),
                read=normalize_symbol(params.get("tape_input")),
            ),
            TransitionOutput(
                state=_text(_require(output, "final_state", None), "final_state"),
                cache=normalize_symbol(output.get("mem_cache_value")),
                write=normalize_symbol(output.get("tape_output")),
                move=Move.parse(output.get("tape_displacement")),
            ),
        )
    except MachineDefinitionError as error:
        raise MachineDefinitionError(f"{where}: {error}") from None


def _parse_simulation_strings(document: Mapping, warnings: List[str]) -> List[str]:
    raw = document.get("simulation_strings")
    if raw is None or raw == "":
        warnings.append("no hay simulation_strings; use --cadena para simular")
        return []
    if not isinstance(raw, list):
        raise MachineDefinitionError("simulation_strings debe ser una lista de cadenas")
    # Una entrada vacía representa la cadena vacía (ε).
    return ["" if s is None else str(s).strip() for s in raw]


_TYPE_NAMES = {Mapping: "un objeto", list: "una lista"}


def _require(mapping: Mapping, key: str, expected: Optional[type], path: str = "") -> Any:
    value = mapping.get(key)
    if value is None or value == "":
        raise MachineDefinitionError(f"falta la llave '{path}{key}'")
    if expected is not None and not isinstance(value, expected):
        raise MachineDefinitionError(f"'{path}{key}' debe ser {_TYPE_NAMES[expected]}")
    return value


def _text(value: Any, field_name: str) -> str:
    if isinstance(value, (Mapping, list)):
        raise MachineDefinitionError(f"'{field_name}' debe ser un texto, no {type(value).__name__}")
    text = "" if value is None else str(value).strip()
    if not text:
        raise MachineDefinitionError(f"'{field_name}' no puede estar vacío")
    return text


def _optional_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
