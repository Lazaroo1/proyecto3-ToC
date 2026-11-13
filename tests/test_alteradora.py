import itertools
import random
import unittest
from pathlib import Path

from turing.loader import load_machine_file
from turing.simulator import Outcome, Simulator

MACHINE = Path(__file__).resolve().parent.parent / "maquinas" / "alteradora_suma_binaria.yaml"


def expected_sum(text: str):
    """Referencia: suma de x+y en binario o None si la entrada no tiene esa forma."""
    if text.count("+") != 1:
        return None
    x, y = text.split("+")
    if not x and not y:
        return None
    return format(int(x or "0", 2) + int(y or "0", 2), "b")


class AlteradoraSumaBinariaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = load_machine_file(MACHINE)
        cls.simulator = Simulator(cls.spec.machine)

    def tape_after(self, text):
        result = self.simulator.run(text)
        self.assertNotEqual(result.outcome, Outcome.STEP_LIMIT, text)
        return "".join(result.final_tape) if result.accepted else None

    def test_definicion_sin_advertencias(self):
        self.assertEqual(self.spec.warnings, [])
        self.assertEqual(len(self.spec.machine.transitions), 43)

    def test_cadenas_del_archivo(self):
        expected = {
            "1011+110": "10001",
            "111+111": "1110",
            "1111+1": "10000",
            "101+1101": "10010",
            "0010+0011": "101",
        }
        self.assertEqual(list(expected), self.spec.simulation_strings)
        for text, result in expected.items():
            with self.subTest(cadena=text):
                self.assertGreaterEqual(len(text), 5)
                self.assertEqual(self.tape_after(text), result)

    def test_el_resultado_no_queda_en_blanks(self):
        for text in self.spec.simulation_strings:
            result = self.simulator.run(text)
            self.assertTrue(result.final_tape)
            self.assertNotIn(None, result.final_tape)

    def test_resultado_cero(self):
        self.assertEqual(self.tape_after("0+0"), "0")
        self.assertEqual(self.tape_after("000+00"), "0")

    def test_un_operando_vacio_cuenta_como_cero(self):
        self.assertEqual(self.tape_after("+101"), "101")
        self.assertEqual(self.tape_after("110+"), "110")

    def test_entradas_mal_formadas_se_rechazan(self):
        for text in ["", "+", "101", "1+1+1", "1++1", "+1+"]:
            with self.subTest(cadena=text):
                self.assertIs(self.simulator.run(text).outcome, Outcome.REJECTED)

    def test_todas_las_cadenas_hasta_longitud_7(self):
        for length in range(8):
            for symbols in itertools.product("01+", repeat=length):
                text = "".join(symbols)
                self.assertEqual(self.tape_after(text), expected_sum(text), text)

    def test_numeros_grandes_aleatorios(self):
        rng = random.Random(24713)
        for _ in range(50):
            x, y = rng.randrange(4096), rng.randrange(4096)
            text = f"{x:b}+{y:b}"
            self.assertEqual(self.tape_after(text), f"{x + y:b}", text)


if __name__ == "__main__":
    unittest.main()
