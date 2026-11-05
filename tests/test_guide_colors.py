import unittest

from core.colors import colore_sfondo_guida


class GuideColorTests(unittest.TestCase):
    def test_blends_program_color_with_background(self):
        self.assertEqual(colore_sfondo_guida("#ffffff", "#000000", 0.5), "#7f7f7f")

    def test_invalid_color_uses_stable_fallback(self):
        self.assertEqual(colore_sfondo_guida("invalid"), "#252030")


if __name__ == "__main__":
    unittest.main()
