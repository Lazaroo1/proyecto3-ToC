import itertools
import unittest
from pathlib import Path

from turing.loader import load_machine_file
from turing.simulator import Outcome, Simulator

MACHINE = Path(__file__).resolve().parent.parent / "maquinas" / "reconocedora_wcw.yaml"


def in_language(text: str) -> bool:
    """Referencia: text ∈ { w#w | w ∈ {a, b, c}+ }."""
    if text.count("#") != 1:
        return False
    left, right = text.split("#")
    return len(left) > 0 and left == right


class ReconocedoraWcwTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = load_machine_file(MACHINE)
        cls.simulator = Simulator(cls.spec.machine)

    def run_string(self, text):
        return self.simulator.run(text)

    def test_definicion_sin_advertencias(self):
        self.assertEqual(self.spec.warnings, [])
        self.assertEqual(len(self.spec.machine.transitions), 33)

    def test_cadenas_del_archivo(self):
        expected = {
            "abc#abc": True,
            "bacab#bacab": True,
            "ccab#ccab": True,
            "abc#acb": False,
            "abca#abc": False,
            "ab#abca": False,
        }
        self.assertEqual(list(expected), self.spec.simulation_strings)
        for text, accepted in expected.items():
            with self.subTest(cadena=text):
                self.assertGreaterEqual(len(text), 5)
                self.assertEqual(self.run_string(text).accepted, accepted)

    def test_ids_iniciales_usan_la_cache(self):
        ids = [str(i) for i in self.run_string("ab#ab").ids[:5]]
        self.assertEqual(
            ids,
            [
                "[q0, B] ab#ab",
                "X [q1, a] b#ab",
                "Xb [q1, a] #ab",
                "Xb# [q2, a] ab",
                "Xb [q3, B] #Xb",
            ],
        )

    def test_aceptacion_termina_en_q7(self):
        result = self.run_string("abc#abc")
        self.assertEqual(result.final_id.state, "q7")
        self.assertEqual(result.final_tape, list("XXX#XXX"))

    def test_rechazos(self):
        for text in ["", "#", "a#", "#a", "abc", "a#b", "ab#ab#ab", "aa#a", "a#aa"]:
            with self.subTest(cadena=text):
                result = self.run_string(text)
                self.assertIs(result.outcome, Outcome.REJECTED)

    def test_simbolo_fuera_del_alfabeto(self):
        self.assertIs(self.run_string("abd#abd").outcome, Outcome.INVALID_INPUT)

    def test_todas_las_cadenas_hasta_longitud_6(self):
        for length in range(7):
            for symbols in itertools.product("abc#", repeat=length):
                text = "".join(symbols)
                result = self.run_string(text)
                self.assertNotEqual(result.outcome, Outcome.STEP_LIMIT, text)
                self.assertEqual(result.accepted, in_language(text), text)


if __name__ == "__main__":
    unittest.main()
