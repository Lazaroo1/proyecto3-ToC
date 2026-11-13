"""Simulador de Máquinas de Turing de una cinta.

Ejemplos:
    python main.py maquinas/reconocedora_wcw.yaml
    python main.py maquinas/alteradora_suma_binaria.yaml --cadena 1011+110
    python main.py maquinas/*.yaml --sin-transiciones
"""

import argparse
import os
import sys
from pathlib import Path
from typing import List, Optional

from turing.errors import MachineDefinitionError
from turing.loader import load_machine_file
from turing.report import Reporter
from turing.simulator import Simulator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="main.py",
        description=(
            "Simulador de Máquinas de Turing de una cinta. Lee la descripción "
            "formal de la MT desde un archivo YAML, simula cada cadena y muestra "
            "sus descripciones instantáneas."
        ),
    )
    parser.add_argument(
        "archivos", nargs="+", type=Path, metavar="ARCHIVO_YAML",
        help="archivo(s) YAML con la descripción de la MT",
    )
    parser.add_argument(
        "-c", "--cadena", action="append", metavar="CADENA",
        help="simular esta cadena en lugar de las de simulation_strings "
             "(se puede repetir; use '' para la cadena vacía)",
    )
    parser.add_argument(
        "-m", "--max-pasos", type=int, default=Simulator.DEFAULT_MAX_STEPS, metavar="N",
        help=f"límite de pasos por cadena (por defecto {Simulator.DEFAULT_MAX_STEPS})",
    )
    parser.add_argument(
        "--sin-transiciones", action="store_true",
        help="no mostrar la transición aplicada junto a cada ID",
    )
    parser.add_argument(
        "--sin-color", action="store_true",
        help="desactivar los colores de la salida",
    )
    return parser


def configure_console() -> None:
    """Fuerza UTF-8 para poder imprimir δ, Σ, Γ y ⊢ también en Windows."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def colors_supported(disabled: bool) -> bool:
    """Colores solo si la salida es una terminal y el usuario no los desactivó."""
    if disabled or "NO_COLOR" in os.environ or not sys.stdout.isatty():
        return False
    if os.name == "nt":
        return _enable_windows_ansi()
    return True


def _enable_windows_ansi() -> bool:
    """Activa las secuencias ANSI (ENABLE_VIRTUAL_TERMINAL_PROCESSING) en Windows."""
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
        mode = ctypes.c_uint32()
        if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            return False
        return bool(kernel32.SetConsoleMode(handle, mode.value | 0x0004))
    except (AttributeError, OSError):
        return False


def main(argv: Optional[List[str]] = None) -> int:
    configure_console()
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.max_pasos < 1:
        parser.error("--max-pasos debe ser al menos 1")

    reporter = Reporter(
        color=colors_supported(args.sin_color),
        show_transitions=not args.sin_transiciones,
    )

    exit_code = 0
    for path in args.archivos:
        try:
            spec = load_machine_file(path)
        except MachineDefinitionError as error:
            sys.stderr.write(reporter.render_error(path, error))
            exit_code = 1
            continue

        sys.stdout.write(reporter.render_header(spec))
        strings = args.cadena if args.cadena is not None else spec.simulation_strings
        simulator = Simulator(spec.machine, max_steps=args.max_pasos)
        for index, text in enumerate(strings, start=1):
            result = simulator.run(text)
            sys.stdout.write(reporter.render_result(index, len(strings), result, spec.machine))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
