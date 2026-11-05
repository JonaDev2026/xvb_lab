import os
import tempfile
import unittest
from unittest.mock import patch

from core import colors


class ColorLogicTests(unittest.TestCase):
    def test_lighten_color_and_preserve_invalid_value(self):
        self.assertEqual(colors.schiarisci("not-a-color"), "not-a-color")
        result = colors.schiarisci("#202020")
        self.assertEqual(len(result), 7)
        self.assertNotEqual(result, "#202020")

    def test_color_cache_version_and_roundtrip(self):
        with tempfile.TemporaryDirectory() as root:
            cache = os.path.join(root, "colors.json")
            with patch.object(colors, "FILE_COLORI", cache):
                colors.scrivi_colori({"channel": "#aabbcc"})
                self.assertEqual(colors.leggi_colori(), {"channel": "#aabbcc"})
                with open(cache, "w", encoding="utf-8") as stream:
                    stream.write('{"_v": 3, "channel": "#aabbcc"}')
                self.assertEqual(colors.leggi_colori(), {})

    def test_svg_conversion_keeps_original_when_not_convertible(self):
        data = b"<svg xmlns=\"http://www.w3.org/2000/svg\"></svg>"
        with patch("subprocess.run", side_effect=OSError), patch.dict("sys.modules", {"cairosvg": None}):
            self.assertEqual(colors.svg_in_png(data), data)
        raw = b"not an svg"
        self.assertIs(colors.svg_in_png(raw), raw)

    def test_playlist_icon_fallback_order(self):
        with tempfile.TemporaryDirectory() as root:
            icons = os.path.join(root, "icone")
            os.makedirs(icons)
            default = os.path.join(icons, "default.png")
            m3u = os.path.join(icons, "m3u.png")
            for path in (default, m3u):
                with open(path, "wb") as stream:
                    stream.write(b"")
            with patch.object(colors, "QUI", root):
                self.assertEqual(colors.immagine_lista(True), m3u)
                os.remove(m3u)
                self.assertEqual(colors.immagine_lista(True), default)


if __name__ == "__main__":
    unittest.main()
