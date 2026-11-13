"""Excepciones del simulador."""


class TuringError(Exception):
    """Error base del simulador de Máquinas de Turing."""


class MachineDefinitionError(TuringError):
    """La descripción formal de la MT (archivo YAML) no es válida."""


class TapeInputError(TuringError):
    """Una cadena de entrada no se puede escribir en la cinta."""
