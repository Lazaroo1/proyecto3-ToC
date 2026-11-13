import unittest

from turing.errors import TapeInputError
from turing.input_parser import parse_input


class ParseInputTest(unittest.TestCase):
    def test_alfabeto_de_un_caracter(self):
        self.assertEqual(
            parse_input("aab#aab", ["a", "b", "#"]),
            ["a", "a", "b", "#", "a", "a", "b"],
        )

    def test_cadena_vacia(self):
        self.assertEqual(parse_input("", ["a"]), [])
        self.assertEqual(parse_input("   ", ["a"]), [])

    def test_ignora_espacios_a_los_lados(self):
        self.assertEqual(parse_input("  101+1 ", ["0", "1", "+"]), ["1", "0", "1", "+", "1"])

    def test_simbolos_de_varios_caracteres_separados_por_espacio(self):
        self.assertEqual(parse_input("q1 q2 #", ["q1", "q2", "#"]), ["q1", "q2", "#"])

    def test_simbolos_de_varios_caracteres_sin_espacios(self):
        self.assertEqual(parse_input("1011", ["1", "10", "11"]), ["10", "11"])

    def test_particion_que_no_es_la_mas_codiciosa(self):
        # Tomar siempre el símbolo más largo ("ab") deja "c" sin pareja;
        # la única partición válida es a + bc.
        self.assertEqual(parse_input("abc", ["a", "ab", "bc"]), ["a", "bc"])

    def test_simbolo_fuera_del_alfabeto(self):
        with self.assertRaisesRegex(TapeInputError, r"'d' \(posición 3\)"):
            parse_input("abd", ["a", "b"])

    def test_simbolo_de_cinta_no_es_de_entrada(self):
        with self.assertRaisesRegex(TapeInputError, "Γ"):
            parse_input("aXb", ["a", "b"], ["a", "b", "X"])

    def test_token_invalido_con_espacios(self):
        with self.assertRaisesRegex(TapeInputError, r"'q3' \(símbolo #2\)"):
            parse_input("q1 q3", ["q1", "q2"])

    def test_el_blank_no_se_usa_para_partir(self):
        self.assertEqual(parse_input("ab", ["a", None, "b"]), ["a", "b"])


if __name__ == "__main__":
    unittest.main()
