import unittest
from pathlib import Path

from turing.loader import load_machine_file
from turing.report import Reporter
from turing.simulator import Simulator

MACHINES = Path(__file__).resolve().parent.parent / "maquinas"


class ReporterTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = load_machine_file(MACHINES / "reconocedora_wcw.yaml")
        simulator = Simulator(cls.spec.machine)
        cls.accepted = simulator.run("ab#ab")
        cls.invalid = simulator.run("ab#abd")

    def test_encabezado_con_la_definicion_formal(self):
        text = Reporter().render_header(self.spec)
        self.assertIn("Reconocedora de w#w", text)
        self.assertIn("Σ  = {a, b, c, #}", text)
        self.assertIn("Γ  = {a, b, c, #, X, B}", text)
        self.assertIn("F  = {q7}", text)

    def test_resultado_lista_ids_y_transiciones(self):
        text = Reporter().render_result(1, 1, self.accepted, self.spec.machine)
        self.assertIn("[q0, B] ab#ab", text)
        # el número de paso se alinea al ancho del último (18 pasos -> 2 columnas)
        self.assertIn("⊢  1   X [q1, a] b#ab", text)
        self.assertIn("⊢ 18   XX#XX [q7, B] B", text)
        self.assertIn("δ([q0, B], a) = ([q1, a], X, R)", text)
        self.assertIn("Resultado: ACEPTADA", text)
        self.assertIn("Cinta final: XX#XX", text)

    def test_sin_transiciones(self):
        text = Reporter(show_transitions=False).render_result(1, 1, self.accepted, self.spec.machine)
        self.assertNotIn("δ(", text)

    def test_sin_color_no_hay_secuencias_ansi(self):
        text = Reporter(color=False).render_result(1, 1, self.accepted, self.spec.machine)
        self.assertNotIn("\033[", text)
        colored = Reporter(color=True).render_result(1, 1, self.accepted, self.spec.machine)
        self.assertIn("\033[", colored)

    def test_resumen(self):
        text = Reporter().render_summary(self.spec, [self.accepted, self.invalid])
        self.assertIn("ab#ab", text)
        self.assertIn("ACEPTADA", text)
        self.assertIn("RECHAZADA (entrada inválida)", text)
        self.assertIn("Aceptadas: 1/2", text)
        self.assertEqual(Reporter().render_summary(self.spec, []), "")


if __name__ == "__main__":
    unittest.main()
