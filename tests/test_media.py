import os
import tempfile
import unittest

from core.media import (
    e_media, nome_url, titolo_url, tipo_url, e_media_url, media_in,
    ore_min_sec, tipo_preferiti, PREF_IPTV, PREF_MUSICA, PREF_VIDEO,
)


class MediaLogicTests(unittest.TestCase):
    def test_local_media_extensions(self):
        self.assertTrue(e_media("film.MKV"))
        self.assertTrue(e_media("brano.flac"))
        self.assertFalse(e_media("lista.m3u"))

    def test_url_names_and_titles(self):
        self.assertEqual(nome_url("https://example.org/video/film.mkv"), "film.mkv")
        self.assertEqual(titolo_url("https://example.org/video/Il_mio-film.mkv"), "Il mio film")

    def test_url_types(self):
        self.assertEqual(tipo_url("https://example.org/a.mp3"), "Audio · MP3 · example.org")
        self.assertEqual(tipo_url("https://example.org/live.m3u8"), "Stream HLS · example.org")
        self.assertTrue(e_media_url("https://example.org/a.mp4"))
        self.assertFalse(e_media_url("https://example.org/live.m3u8"))

    def test_media_walk_skips_hidden_entries(self):
        with tempfile.TemporaryDirectory() as root:
            os.makedirs(os.path.join(root, ".hidden"))
            os.makedirs(os.path.join(root, "Album"))
            for path in ("b.mp3", "Album/a.flac", ".hidden/c.mp3", ".skip.mp4"):
                target = os.path.join(root, path)
                with open(target, "wb") as stream:
                    stream.write(b"")
            result = media_in(root)
            self.assertEqual([os.path.basename(item[1]) for item in result], ["b.mp3", "a.flac"])

    def test_time_format(self):
        self.assertEqual(ore_min_sec(125), "02:05")
        self.assertEqual(ore_min_sec(3723), "1:02:03")
        self.assertEqual(ore_min_sec(-1), "00:00")

    def test_favorite_categories(self):
        self.assertEqual(tipo_preferiti("https://example.org/live"), PREF_IPTV)
        self.assertEqual(tipo_preferiti("/tmp/song.mp3"), PREF_MUSICA)
        self.assertEqual(tipo_preferiti("/tmp/movie.mkv"), PREF_VIDEO)


if __name__ == "__main__":
    unittest.main()
