import unittest
from unittest.mock import patch

from core.system import font_desktop_sistema


class DesktopFontTests(unittest.TestCase):
    def test_reads_gnome_font_family_style_and_weight(self):
        with patch("core.system.subprocess.check_output", return_value="'Cantarell Bold Italic 11'"):
            self.assertEqual(font_desktop_sistema(), ("Cantarell", "italic", "bold"))

    def test_reads_xfce_font_when_gnome_is_unavailable(self):
        def risposta(comando, **kwargs):
            if comando[0] == "gsettings":
                raise OSError("not available")
            return "Noto Sans 10"
        with patch("core.system.subprocess.check_output", side_effect=risposta):
            self.assertEqual(font_desktop_sistema(), ("Noto Sans", "normal", "normal"))

    def test_fallback_when_no_desktop_font_is_available(self):
        with patch("core.system.subprocess.check_output", side_effect=OSError):
            with patch("core.system.Path.home", return_value=__import__("pathlib").Path("/nonexistent")):
                self.assertEqual(font_desktop_sistema(), (None, "normal", "normal"))


if __name__ == "__main__":
    unittest.main()
