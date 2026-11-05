import os
import tempfile
import unittest
from unittest.mock import patch

from core import thumbnails


@unittest.skipUnless(thumbnails.HA_PIL, "Pillow not installed")
class ThumbnailTests(unittest.TestCase):
    def test_local_video_poster_is_cached(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as root:
            video = os.path.join(root, "Film.mkv")
            poster = os.path.join(root, "Film.jpg")
            cache = os.path.join(root, "cache")
            with open(video, "wb") as stream:
                stream.write(b"video")
            Image.new("RGB", (400, 300), "red").save(poster)
            with patch.object(thumbnails, "CACHE_ANTEPRIME", cache):
                result = thumbnails.anteprima_di(video)
                self.assertTrue(result and os.path.isfile(result))
                self.assertEqual(thumbnails.anteprima_di(video), result)

    def test_missing_media_returns_none(self):
        with tempfile.TemporaryDirectory() as root:
            with patch.object(thumbnails, "CACHE_ANTEPRIME", os.path.join(root, "cache")):
                self.assertIsNone(thumbnails.anteprima_di(os.path.join(root, "missing.mkv")))

    def test_video_without_local_poster_uses_ffmpeg(self):
        with tempfile.TemporaryDirectory() as root:
            video = os.path.join(root, "Film.mkv")
            with open(video, "wb") as stream:
                stream.write(b"video")
            with patch.object(thumbnails, "CACHE_ANTEPRIME", os.path.join(root, "cache")), \
                 patch.object(thumbnails.subprocess, "run", side_effect=TimeoutError):
                self.assertIsNone(thumbnails.anteprima_di(video))


if __name__ == "__main__":
    unittest.main()
