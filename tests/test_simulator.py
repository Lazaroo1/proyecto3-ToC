import unittest
from pathlib import Path

from turing.loader import load_machine_file, load_machine_text
from turing.simulator import Outcome, Simulator
from turing.symbols import BLANK

FIXTURES = Path(__file__).resolve().parent / "fixtures"

# Acepta a*b; va marcando las a con X.
A_STAR_B = """
q_states: {q_list: [q0, q1], initial: q0, final: q1}
alphabet: [a, b]
tape_alphabet: [a, b, X, ]
delta:
- params: {initial_state: q0, tape_input: a}
  output: {final_state: q0, tape_output: X, tape_displacement: R}
- params: {initial_state: q0, tape_input: b}
  output: {final_state: q1, tape_output: b, tape_displacement: S}
"""

# Copia el primer símbolo al final de la cadena usando la caché:
#   ab -> aba,  ba -> bab
COPY_FIRST = """
q_states: {q_list: [q0, q1, q2], initial: q0, final: q2}
alphabet: [a, b]
tape_alphabet: [a, b, ]
delta:
- params: {initial_state: q0, mem_cache_value: , tape_input: a}
  output: {final_state: q1, mem_cache_value: a, tape_output: a, tape_displacement: R}
- params: {initial_state: q0, mem_cache_value: , tape_input: b}
  output: {final_state: q1, mem_cache_value: b, tape_output: b, tape_displacement: R}
- params: {initial_state: q1, mem_cache_value: a, tape_input: a}
  output: {final_state: q1, mem_cache_value: a, tape_output: a, tape_displacement: R}
- params: {initial_state: q1, mem_cache_value: a, tape_input: b}
  output: {final_state: q1, mem_cache_value: a, tape_output: b, tape_displacement: R}
- params: {initial_state: q1, mem_cache_value: b, tape_input: a}
  output: {final_state: q1, mem_cache_value: b, tape_output: a, tape_displacement: R}
- params: {initial_state: q1, mem_cache_value: b, tape_input: b}
  output: {final_state: q1, mem_cache_value: b, tape_output: b, tape_displacement: R}
- params: {initial_state: q1, mem_cache_value: a, tape_input: }
  output: {final_state: q2, mem_cache_value: , tape_output: a, tape_displacement: S}
- params: {initial_state: q1, mem_cache_value: b, tape_input: }
  output: {final_state: q2, mem_cache_value: , tape_output: b, tape_displacement: S}
"""

# Escribe un 1 a la izquierda de la entrada (la cinta crece a la izquierda).
PREPEND_ONE = """
q_states: {q_list: [q0, q1], initial: q0, final: q1}
alphabet: ['0', '1']
tape_alphabet: ['0', '1', ]
delta:
- params: {initial_state: q0, tape_input: '0'}
  output: {final_state: q0, tape_output: '0', tape_displacement: L}
- params: {initial_state: q0, tape_input: }
  output: {final_state: q1, tape_output: '1', tape_displacement: S}
"""

# Nunca se detiene: avanza a la derecha para siempre.
LOOP = """
q_states: {q_list: [q0, q1], initial: q0, final: q1}
alphabet: [a]
tape_alphabet: [a, ]
delta:
- params: {initial_state: q0, tape_input: a}
  output: {final_state: q0, tape_output: a, tape_displacement: R}
- params: {initial_state: q0, tape_input: }
  output: {final_state: q0, tape_output: , tape_displacement: R}
"""


def simulator(text: str, **kwargs) -> Simulator:
    return Simulator(load_machine_text(text).machine, **kwargs)


class SimulatorTest(unittest.TestCase):
    def test_acepta_y_lista_todas_las_ids(self):
        result = simulator(A_STAR_B).run("aab")
        self.assertIs(result.outcome, Outcome.ACCEPTED)
        self.assertTrue(result.accepted)
        self.assertEqual(result.steps, 3)
        self.assertEqual(
            [str(i) for i in result.ids],
            ["[q0, B] aab", "X [q0, B] ab", "XX [q0, B] b", "XX [q1, B] b"],
        )
        self.assertIsNone(result.ids[0].transition)
        self.assertEqual(str(result.ids[1].transition), "δ([q0, B], a) = ([q0, B], X, R)")
        self.assertEqual(result.final_tape, ["X", "X", "b"])

    def test_rechaza_cuando_no_hay_transicion(self):
        result = simulator(A_STAR_B).run("aa")
        self.assertIs(result.outcome, Outcome.REJECTED)
        self.assertFalse(result.accepted)
        self.assertIn("δ([q0, B], B)", result.message)
        self.assertEqual(str(result.final_id), "XX [q0, B] B")

    def test_cadena_vacia(self):
        result = simulator(A_STAR_B).run("")
        self.assertIs(result.outcome, Outcome.REJECTED)
        self.assertEqual([str(i) for i in result.ids], ["[q0, B] B"])

    def test_entrada_invalida_no_se_simula(self):
        result = simulator(A_STAR_B).run("abc")
        self.assertIs(result.outcome, Outcome.INVALID_INPUT)
        self.assertEqual(result.ids, [])
        self.assertIn("'c'", result.message)

    def test_cache_guarda_un_simbolo(self):
        sim = simulator(COPY_FIRST)
        result = sim.run("ab")
        self.assertTrue(result.accepted)
        self.assertEqual(result.final_tape, ["a", "b", "a"])
        self.assertEqual(str(result.ids[1]), "a [q1, a] b")
        self.assertEqual(sim.run("bba").final_tape, ["b", "b", "a", "b"])

    def test_la_cinta_crece_a_la_izquierda(self):
        result = simulator(PREPEND_ONE).run("0")
        self.assertTrue(result.accepted)
        self.assertEqual(result.final_tape, ["1", "0"])
        self.assertEqual(str(result.ids[1]), "[q0, B] B0")

    def test_limite_de_pasos(self):
        result = simulator(LOOP, max_steps=50).run("aaa")
        self.assertIs(result.outcome, Outcome.STEP_LIMIT)
        self.assertFalse(result.accepted)
        self.assertEqual(result.steps, 50)

    def test_max_steps_invalido(self):
        with self.assertRaises(ValueError):
            simulator(LOOP, max_steps=0)

    def test_paso_a_paso(self):
        sim = simulator(A_STAR_B)
        config = sim.initial_configuration(["a", "b"])
        self.assertEqual((config.state, config.cache, config.tape.read()), ("q0", BLANK, "a"))
        transition = sim.step(config)
        self.assertEqual(transition.output.write, "X")
        self.assertEqual((config.state, config.steps, config.tape.read()), ("q0", 1, "b"))
        sim.step(config)
        self.assertEqual(config.state, "q1")

    def test_ejemplo_del_enunciado_rechaza_simbolos_fuera_de_sigma(self):
        spec = load_machine_file(FIXTURES / "ejemplo_enunciado.yaml")
        sim = Simulator(spec.machine)
        # En el ejemplo '#' solo está en Γ, así que aab#aab no es una entrada válida
        result = sim.run(spec.simulation_strings[0])
        self.assertIs(result.outcome, Outcome.INVALID_INPUT)
        # y como el ejemplo está incompleto, ab se rechaza tras un paso
        result = sim.run("ab")
        self.assertIs(result.outcome, Outcome.REJECTED)
        self.assertEqual(result.steps, 1)


if __name__ == "__main__":
    unittest.main()
