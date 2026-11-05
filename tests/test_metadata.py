import json
import os
import tempfile
import unittest

from core.metadata import (
    titolo_anno, _anno_via, dal_percorso, poster_film,
    leggi_json, scrivi_json, copertina_url,
)


class MetadataLogicTests(unittest.TestCase):
    def test_title_and_year_from_filename_and_folder(self):
        self.assertEqual(titolo_anno("/films/Neon.Harbour.2023.1080p.mkv"), ("Neon Harbour", "2023"))
        self.assertEqual(titolo_anno("/films/Neon.Harbour.mkv"), ("Neon Harbour", None))
        self.assertEqual(titolo_anno("/films/Arrival (2016)/movie.mkv"), ("Arrival", "2016"))

    def test_year_extraction_variants(self):
        self.assertEqual(_anno_via("Terremoto (1993)"), ("Terremoto", "1993"))
        self.assertEqual(_anno_via("[1993] Terremoto"), ("Terremoto", "1993"))
        self.assertEqual(_anno_via("1993 - Terremoto"), ("Terremoto", "1993"))
        self.assertEqual(_anno_via("Terremoto - 1993"), ("Terremoto", "1993"))

    def test_music_metadata_from_directory_layout(self):
        self.assertEqual(
            dal_percorso("/music/Artist/Album (1993)/01 - Track_Name.flac"),
            ("Track Name", "Artist", "Album", "1993")
        )
        self.assertEqual(
            dal_percorso("/music/Artist - Album/01. Track.mp3"),
            ("Track", "Artist", "Album", "")
        )

    def test_local_poster_priority_and_json_cache(self):
        with tempfile.TemporaryDirectory() as root:
            movie = os.path.join(root, "Film.mkv")
            with open(movie, "wb") as stream:
                stream.write(b"")
            poster = os.path.join(root, "Film.jpg")
            with open(poster, "wb") as stream:
                stream.write(b"image")
            self.assertEqual(poster_film(movie), poster)
            cache = os.path.join(root, "cache", "data.json")
            scrivi_json(cache, {"value": 42})
            self.assertEqual(leggi_json(cache), {"value": 42})
            self.assertEqual(leggi_json(os.path.join(root, "missing.json")), {})

    def test_cover_cache_path_is_stable(self):
        self.assertEqual(copertina_url("https://example.org/cover"),
                         copertina_url("https://example.org/cover"))


if __name__ == "__main__":
    unittest.main()
