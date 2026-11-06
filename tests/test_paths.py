import os
import unittest

from core.config import (
    CACHE_DIR, CARTELLE_LISTE, CONFIG, CONFIG_DIR, DATA_DIR,
    PORTA, REGISTRAZIONI,
)
from core.constants import VERSIONE


class XVB5PathsTests(unittest.TestCase):
    def test_application_version_is_5(self):
        self.assertEqual(VERSIONE, "5.0.0")

    def test_config_cache_and_data_use_only_xvb5_roots(self):
        home = os.path.expanduser("~")
        self.assertEqual(CONFIG_DIR, os.path.join(home, ".config", "xvb5"))
        self.assertEqual(CACHE_DIR, os.path.join(home, ".cache", "xvb5"))
        self.assertEqual(DATA_DIR, os.path.join(home, ".local", "share", "xvb5"))
        self.assertEqual(CONFIG, os.path.join(CONFIG_DIR, "xvb5.json"))

    def test_persistent_application_paths_are_inside_xvb5_roots(self):
        self.assertEqual(os.path.dirname(PORTA), CACHE_DIR)
        self.assertEqual(os.path.dirname(REGISTRAZIONI), DATA_DIR)
        self.assertEqual(CARTELLE_LISTE, (os.path.join(DATA_DIR, "playlists"),))


if __name__ == "__main__":
    unittest.main()
