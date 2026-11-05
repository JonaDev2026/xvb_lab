import unittest

from core import artwork


@unittest.skipUnless(artwork.HA_PIL, "Pillow not installed")
class ArtworkTests(unittest.TestCase):
    def test_vinyl_frame_is_transparent_and_centered(self):
        from PIL import Image
        base = Image.new("RGBA", (64, 64), (180, 30, 80, 255))
        result = artwork.disco_frame(base, 80, 64, 0, "#30a0d0")
        self.assertEqual(result.size, (80, 64))
        self.assertEqual(result.getpixel((0, 0))[3], 0)
        self.assertGreater(result.getpixel((40, 32))[3], 0)

    def test_sidebar_icons_keep_requested_dimensions(self):
        for funzione in (artwork.cartellina, artwork.segnalibro, artwork.globo,
                         artwork.disco, artwork.vinile, artwork.pallino):
            immagine = funzione("#aabbcc", lato=32)
            self.assertIsNotNone(immagine)
            self.assertEqual(immagine.size, (32, 32))

    def test_quality_labels_and_colors(self):
        self.assertEqual(artwork.qualita(2160, 0), ("2160p", "#bf5af2"))
        self.assertEqual(artwork.qualita(1080, 0), ("1080p", "#30d158"))
        self.assertEqual(artwork.qualita(720, 0), ("720p", "#0a84ff"))
        self.assertEqual(artwork.qualita(0, 250000), ("250 kbit/s", "#9e9e9e"))


if __name__ == "__main__":
    unittest.main()
