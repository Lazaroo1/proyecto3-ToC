import unittest

from turing.symbols import BLANK
from turing.tape import Tape
from turing.transition import Move


class TapeTest(unittest.TestCase):
    def test_cabezal_inicia_en_el_primer_simbolo(self):
        tape = Tape(["a", "b", "c"])
        self.assertEqual(tape.head, 0)
        self.assertEqual(tape.read(), "a")

    def test_cinta_vacia_lee_blank(self):
        tape = Tape()
        self.assertIs(tape.read(), BLANK)
        self.assertTrue(tape.is_empty())
        self.assertEqual(tape.content(), [])

    def test_escribir_y_mover(self):
        tape = Tape(["a", "b"])
        tape.write("X")
        tape.move(Move.RIGHT)
        self.assertEqual(tape.read(), "b")
        tape.move(Move.STAY)
        self.assertEqual(tape.read(), "b")
        self.assertEqual(tape.content(), ["X", "b"])

    def test_crece_hacia_la_izquierda(self):
        tape = Tape(["a"])
        tape.move(Move.LEFT)
        self.assertIs(tape.read(), BLANK)
        tape.write("1")
        self.assertEqual(tape.content(), ["1", "a"])
        self.assertEqual(tape.head, -1)

    def test_crece_hacia_la_derecha(self):
        tape = Tape(["a"])
        for _ in range(3):
            tape.move(Move.RIGHT)
        tape.write("Z")
        self.assertEqual(tape.content(), ["a", BLANK, BLANK, "Z"])

    def test_escribir_blank_borra_la_celda(self):
        tape = Tape(["a", "b"])
        tape.write(BLANK)
        self.assertEqual(tape.content(), ["b"])
        tape.move(Move.RIGHT)
        tape.write(BLANK)
        self.assertTrue(tape.is_empty())

    def test_split_at_head_incluye_el_simbolo_bajo_el_cabezal(self):
        tape = Tape(["a", "b", "c"])
        tape.move(Move.RIGHT)
        self.assertEqual(tape.split_at_head(), (["a"], ["b", "c"]))

    def test_split_at_head_con_cabezal_fuera_del_contenido(self):
        tape = Tape(["a", "b"])
        tape.move(Move.RIGHT)
        tape.move(Move.RIGHT)
        self.assertEqual(tape.split_at_head(), (["a", "b"], [BLANK]))
        tape = Tape(["a", "b"])
        tape.move(Move.LEFT)
        self.assertEqual(tape.split_at_head(), ([], [BLANK, "a", "b"]))

    def test_copy_es_independiente(self):
        tape = Tape(["a"])
        clone = tape.copy()
        clone.write("b")
        clone.move(Move.RIGHT)
        self.assertEqual(tape.read(), "a")
        self.assertEqual(tape.head, 0)


if __name__ == "__main__":
    unittest.main()
