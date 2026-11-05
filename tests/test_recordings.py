import os
import tempfile
import unittest
from unittest.mock import patch

from core import recordings


class RecordingTests(unittest.TestCase):
    def test_groups_recordings_by_channel_and_date(self):
        with tempfile.TemporaryDirectory() as root:
            channel = os.path.join(root, "News")
            os.mkdir(channel)
            paths = [os.path.join(channel, "Evening News - 2026-11-05 20-30.mkv"),
                     os.path.join(root, "Loose - 2026-11-04 19-00.ts")]
            for path in paths:
                with open(path, "wb") as stream:
                    stream.write(b"x")
            with patch.object(recordings, "REGISTRAZIONI", root):
                result = recordings.registrazioni()
            self.assertEqual(result[0][0], ("News", "2026-11-05"))
            self.assertEqual(result[0][1][0][:2], ("20:30", "Evening News"))
            self.assertEqual(result[1][0], ("xvb", "2026-11-04"))

    def test_empty_recording_directory(self):
        with patch.object(recordings, "REGISTRAZIONI", "/path/that/does/not/exist"):
            self.assertEqual(recordings.registrazioni(), [])

    def test_version_comparison_is_numeric(self):
        self.assertTrue(recordings.piu_nuova("1.10", "1.9"))
        self.assertFalse(recordings.piu_nuova("1.9", "1.10"))
        self.assertTrue(recordings.piu_nuova("2.0-1", "2.0"))


if __name__ == "__main__":
    unittest.main()
