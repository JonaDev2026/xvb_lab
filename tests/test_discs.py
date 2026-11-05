import os
import tempfile
import unittest

from core.discs import dvd_cifrato, e_cd, e_dvd, titolo_da_etichetta


class DiscDetectionTests(unittest.TestCase):
    def test_cd_uri_detection(self):
        self.assertTrue(e_cd("cdda://1"))
        self.assertFalse(e_cd("https://example.org/live"))

    def test_dvd_directory_detection(self):
        with tempfile.TemporaryDirectory() as root:
            self.assertFalse(e_dvd(root))
            os.mkdir(os.path.join(root, "VIDEO_TS"))
            self.assertTrue(e_dvd(root))

    def test_encrypted_or_unreadable_dvd_is_conservatively_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            os.mkdir(os.path.join(root, "VIDEO_TS"))
            self.assertTrue(dvd_cifrato(root))
            with open(os.path.join(root, "VIDEO_TS", "VTS_01_1.VOB"), "wb") as stream:
                stream.write(b"not a dvd packet")
            self.assertTrue(dvd_cifrato(root))

    def test_disc_label_cleanup(self):
        self.assertEqual(titolo_da_etichetta("BACK_FUTURE_3_DISC_1"), "Back Future 3")
        self.assertEqual(titolo_da_etichetta("MY_MOVIE_DVD9_PAL"), "My Movie")


if __name__ == "__main__":
    unittest.main()
