import os
import tempfile
import unittest
from unittest.mock import patch

from core import playlists


class PlaylistTests(unittest.TestCase):
    def test_playlist_detection_and_discovery(self):
        with tempfile.TemporaryDirectory() as root:
            path = os.path.join(root, "channels.data")
            with open(path, "w", encoding="utf-8") as stream:
                stream.write("#EXTM3U\n#EXTINF:-1,Channel\nhttps://example.org/live\n")
            self.assertTrue(playlists.e_una_lista(path))
            self.assertEqual(playlists.liste_in(root), [path])

    def test_original_m3u_parser_preserves_metadata(self):
        with tempfile.TemporaryDirectory() as root:
            source = os.path.join(root, "master.m3u")
            cache = os.path.join(root, "cache")
            with open(source, "w", encoding="utf-8") as stream:
                stream.write(
                    '#EXTM3U\n'
                    '#EXTINF:-1 tvg-id="news.id" tvg-logo="https://example.org/logo.png" group-title="News",News One\n'
                    'https://example.org/news\n'
                    '#EXTINF:-1 group-title="Movies" license-type="clearkey" license-details="abc:def",Movie One\n'
                    'https://example.org/movie\n'
                )
            with patch.object(playlists, "CACHE_LISTE", cache):
                playlists._CACHE_PARSED_MEMORIA.clear()
                channels = playlists.leggi_lista(source)
                self.assertEqual(channels, [
                    ("News One", "https://example.org/news", "news.id"),
                    ("Movie One", "https://example.org/movie", None),
                ])
                self.assertEqual(playlists.LOGHI["https://example.org/news"], "https://example.org/logo.png")
                self.assertEqual(playlists.CHIAVI["https://example.org/movie"], "abc:def")
                self.assertEqual(playlists.categorie_m3u(source), {
                    "https://example.org/news": "News",
                    "https://example.org/movie": "Movies",
                })

    def test_empty_playlist_data_for_missing_file(self):
        result = playlists._dati_lista("/path/that/does/not/exist.m3u", solo_cache=True)
        self.assertEqual(result, {"canali": [], "categorie": {}, "loghi": {}, "chiavi": {}})


if __name__ == "__main__":
    unittest.main()
