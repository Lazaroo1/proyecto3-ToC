import textwrap
import unittest
from pathlib import Path

from turing.errors import MachineDefinitionError
from turing.loader import load_machine_file, load_machine_text
from turing.symbols import BLANK
from turing.transition import Move

FIXTURES = Path(__file__).resolve().parent / "fixtures"

BASE = """
q_states:
  q_list: ['0', '1']
  initial: '0'
  final: '1'
alphabet: [a]
tape_alphabet: [a, X, ]
"""


def load(extra: str, base: str = BASE):
    return load_machine_text(textwrap.dedent(base) + textwrap.dedent(extra))


class EjemploEnunciadoTest(unittest.TestCase):
    def setUp(self):
        self.spec = load_machine_file(FIXTURES / "ejemplo_enunciado.yaml")
        self.machine = self.spec.machine

    def test_estados(self):
        self.assertEqual(self.machine.states, ["0", "1", "2", "3", "4", "5"])
        self.assertEqual(self.machine.initial_state, "0")
        self.assertEqual(self.machine.final_states, ["5"])

    def test_alfabetos(self):
        self.assertEqual(self.machine.input_alphabet, ["a", "b"])
        # Σ ⊆ Γ: a y b se agregan aunque el ejemplo no los liste en tape_alphabet
        self.assertEqual(set(self.machine.tape_alphabet), {"a", "b", "#", "X"})
        self.assertTrue(any("Σ ⊆ Γ" in w for w in self.spec.warnings))

    def test_transiciones(self):
        self.assertEqual(len(self.machine.transitions), 2)
        t = self.machine.transition_for("0", BLANK, "a")
        self.assertEqual(t.output.state, "1")
        self.assertEqual(t.output.cache, "a")
        self.assertIs(t.output.write, BLANK)
        self.assertIs(t.output.move, Move.RIGHT)
        self.assertEqual(t.format(), "δ([0, B], a) = ([1, a], B, R)")
        self.assertEqual(
            str(self.machine.transition_for("0", BLANK, "b")),
            "δ([0, B], b) = ([1, b], B, R)",
        )

    def test_cadenas_y_origen(self):
        self.assertEqual(self.spec.simulation_strings, ["aab#aab", "ab#ab", "abbababa#aba"])
        self.assertEqual(self.spec.title, "ejemplo_enunciado.yaml")


class LoaderTest(unittest.TestCase):
    def test_valores_numericos_se_conservan_como_texto(self):
        spec = load(
            """
            delta: []
            simulation_strings:
            - 0101
            - 10
            -
            """,
            base="""
            q_states:
              q_list: [0, 1]
              initial: 0
              final: [1]
            alphabet: [0, 1]
            tape_alphabet: [0, 1, ]
            """,
        )
        self.assertEqual(spec.machine.states, ["0", "1"])
        self.assertEqual(spec.machine.input_alphabet, ["0", "1"])
        self.assertEqual(spec.simulation_strings, ["0101", "10", ""])

    def test_varios_estados_finales(self):
        spec = load_machine_text(
            "q_states: {q_list: [a, b, c], initial: a, final: [b, c]}\n"
            "alphabet: [x]\ntape_alphabet: [x]\ndelta: []\n"
        )
        self.assertEqual(spec.machine.final_states, ["b", "c"])

    def test_nombre_y_descripcion_opcionales(self):
        spec = load("name: Mi MT\ndescription: prueba\ndelta: []\n")
        self.assertEqual(spec.title, "Mi MT")
        self.assertEqual(spec.machine.description, "prueba")

    def test_llave_desconocida_genera_advertencia(self):
        spec = load("delta: []\notra_cosa: 1\n")
        self.assertTrue(any("otra_cosa" in w for w in spec.warnings))

    def test_falta_llave_obligatoria(self):
        with self.assertRaisesRegex(MachineDefinitionError, "delta"):
            load("")

    def test_yaml_invalido(self):
        with self.assertRaisesRegex(MachineDefinitionError, "YAML no es válido"):
            load_machine_text("q_states: [")

    def test_desplazamiento_invalido(self):
        with self.assertRaisesRegex(MachineDefinitionError, r"delta\[1\].*L, R o S"):
            load(
                """
                delta:
                - params: {initial_state: '0', tape_input: a}
                  output: {final_state: '1', tape_output: X, tape_displacement: D}
                """
            )

    def test_estado_inexistente(self):
        with self.assertRaisesRegex(MachineDefinitionError, "'9' no está en q_list"):
            load(
                """
                delta:
                - params: {initial_state: '9', tape_input: a}
                  output: {final_state: '1', tape_output: X, tape_displacement: R}
                """
            )

    def test_simbolo_fuera_de_gamma(self):
        with self.assertRaisesRegex(MachineDefinitionError, "'Z' no pertenece"):
            load(
                """
                delta:
                - params: {initial_state: '0', tape_input: a}
                  output: {final_state: '1', tape_output: Z, tape_displacement: R}
                """
            )

    def test_no_determinista(self):
        with self.assertRaisesRegex(MachineDefinitionError, "no es determinista"):
            load(
                """
                delta:
                - params: {initial_state: '0', tape_input: a}
                  output: {final_state: '1', tape_output: X, tape_displacement: R}
                - params: {initial_state: '0', tape_input: a}
                  output: {final_state: '0', tape_output: X, tape_displacement: L}
                """
            )

    def test_cache_vacio_y_null_son_blank(self):
        spec = load(
            """
            delta:
            - params: {initial_state: '0', mem_cache_value: null, tape_input: a}
              output: {final_state: '1', mem_cache_value: ~, tape_output: , tape_displacement: S}
            """
        )
        t = spec.machine.transitions[0]
        self.assertIs(t.params.cache, BLANK)
        self.assertIs(t.output.cache, BLANK)
        self.assertIs(t.output.write, BLANK)

    def test_archivo_inexistente(self):
        with self.assertRaisesRegex(MachineDefinitionError, "no se pudo leer"):
            load_machine_file(FIXTURES / "no_existe.yaml")


if __name__ == "__main__":
    unittest.main()
