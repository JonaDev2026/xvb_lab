import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from core import tags


class TagLogicTests(unittest.TestCase):
    def test_missing_file_returns_empty_tags(self):
        self.assertEqual(tags.tag_di("/missing/audio.mp3", {}), ("", "", "", ""))

    def test_cached_tags_are_reused(self):
        with tempfile.NamedTemporaryFile() as stream:
            cached = [os.path.getmtime(stream.name), "Title", "Artist", "Album", "1999"]
            with patch.object(tags, "HA_TAG", True), patch.object(tags, "mutagen", create=True) as mutagen:
                cache = {stream.name: cached}
                self.assertEqual(tags.tag_di(stream.name, cache), ("Title", "Artist", "Album", "1999"))
                mutagen.File.assert_not_called()

    def test_reads_and_caches_mutagen_tags(self):
        with tempfile.NamedTemporaryFile() as stream:
            data = SimpleNamespace(tags={
                "title": ["Title"], "artist": ["Artist"],
                "album": ["Album"], "date": ["2001-05-04"],
            })
            with patch.object(tags, "HA_TAG", True), patch.object(tags, "mutagen", create=True) as mutagen:
                mutagen.File.return_value = data
                cache = {}
                self.assertEqual(tags.tag_di(stream.name, cache), ("Title", "Artist", "Album", "2001"))
                self.assertEqual(tags.tag_di(stream.name, cache), ("Title", "Artist", "Album", "2001"))
                mutagen.File.assert_called_once_with(stream.name, easy=True)


if __name__ == "__main__":
    unittest.main()
