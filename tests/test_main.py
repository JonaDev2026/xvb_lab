import os
import unittest
from unittest.mock import patch

from main import argomenti_avvio, percorso_istanza
from core.single_instance import PORTA


class MainStartupTests(unittest.TestCase):
    def test_regular_arguments_preserve_file_paths(self):
        argomenti, nuova = argomenti_avvio(["/tmp/movie.mkv"])
        self.assertEqual(argomenti, ["/tmp/movie.mkv"])
        self.assertFalse(nuova)

    def test_secondary_instance_flag_is_not_treated_as_a_file(self):
        argomenti, nuova = argomenti_avvio(["--nuova-istanza", "/tmp/movie.mkv"])
        self.assertEqual(argomenti, ["/tmp/movie.mkv"])
        self.assertTrue(nuova)

    def test_default_instance_uses_standard_socket(self):
        self.assertEqual(percorso_istanza(False), PORTA)

    def test_secondary_instance_uses_a_distinct_process_socket(self):
        with patch("main.os.getpid", return_value=12345):
            percorso = percorso_istanza(True)
        self.assertEqual(
            percorso,
            os.path.join(os.path.dirname(PORTA), "xvb5-12345.sock"))
        self.assertNotEqual(percorso, PORTA)


if __name__ == "__main__":
    unittest.main()
