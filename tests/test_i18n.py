import unittest

from i18n import _, imposta_lingua, lingua_corrente
from i18n.traduzioni import LINGUE, TESTI


class TranslationTests(unittest.TestCase):
    def tearDown(self):
        imposta_lingua("en")

    def test_english_is_default(self):
        self.assertEqual(lingua_corrente(), "en")
        self.assertEqual(_("Open file..."), "Open file...")

    def test_all_original_languages_are_available(self):
        self.assertEqual({code for code, _name in LINGUE}, {"en", "it", "es", "fr", "de", "pt", "ru"})
        for code, _name in LINGUE:
            if code != "en":
                self.assertIn(code, TESTI)

    def test_italian_translation(self):
        imposta_lingua("it")
        self.assertEqual(_("Open file..."), "Apri file...")

    def test_unknown_language_falls_back_to_system(self):
        self.assertIn(imposta_lingua("xx"), dict(LINGUE))


if __name__ == "__main__":
    unittest.main()
