import os
import tempfile
import unittest
from unittest.mock import patch

from core import favorites, playlists


class FavoritesTests(unittest.TestCase):
    def test_save_and_read_favorites_with_metadata(self):
        with tempfile.TemporaryDirectory() as root:
            lists = os.path.join(root, "playlists")
            os.makedirs(lists)
            url = "https://example.org/live"
            playlists.CHIAVI[url] = "key-id:key-value"
            try:
                with patch.object(favorites, "CARTELLE_LISTE", (lists,)):
                    favorites.scrivi_preferiti([
                        ("Channel One", url, "channel.id", "News")
                    ])
                    path = os.path.join(lists, "favorite", "iptv.m3u")
                    with open(path, encoding="utf-8") as stream:
                        data = stream.read()
                    self.assertIn('tvg-id="channel.id"', data)
                    self.assertIn('license-type="clearkey"', data)
                    self.assertIn('group-title="News"', data)
                    self.assertEqual(favorites.leggi_preferiti(), [
                        ("Channel One", url, "channel.id")
                    ])
                    self.assertEqual(favorites.leggi_preferiti_cat(), [
                        ("Channel One", url, "channel.id", "News")
                    ])
            finally:
                playlists.CHIAVI.pop(url, None)

    def test_legacy_favorites_file_is_renamed(self):
        with tempfile.TemporaryDirectory() as root:
            lists = os.path.join(root, "playlists")
            legacy_dir = os.path.join(lists, "favorite")
            os.makedirs(legacy_dir)
            old = os.path.join(legacy_dir, "favorite.m3u")
            with open(old, "w", encoding="utf-8") as stream:
                stream.write("#EXTM3U\n")
            with patch.object(favorites, "CARTELLE_LISTE", (lists,)):
                new = favorites.file_preferiti()
                self.assertTrue(os.path.isfile(new))
                self.assertFalse(os.path.exists(old))


if __name__ == "__main__":
    unittest.main()
