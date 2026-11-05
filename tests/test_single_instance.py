import os
import tempfile
import time
import unittest

from PySide6.QtCore import QCoreApplication

from core.single_instance import porta_unica


class SingleInstanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def _attendi(self, condizione):
        fine = time.monotonic() + 2
        while time.monotonic() < fine:
            self.app.processEvents()
            if condizione():
                return True
            time.sleep(0.01)
        return condizione()

    def test_second_launch_forwards_files_to_existing_instance(self):
        with tempfile.TemporaryDirectory() as root:
            percorso = os.path.join(root, "xvb.sock")
            server = porta_unica([], percorso)
            ricevuti = []
            server.files.connect(ricevuti.append)
            file_media = os.path.join(root, "film.mkv")
            self.assertIsNone(porta_unica([file_media], percorso))
            self.assertTrue(self._attendi(lambda: bool(ricevuti)))
            self.assertEqual(ricevuti, [[file_media]])
            server.close()

    def test_second_launch_without_arguments_raises_existing_window(self):
        with tempfile.TemporaryDirectory() as root:
            percorso = os.path.join(root, "xvb.sock")
            server = porta_unica([], percorso)
            richieste = []
            server.raise_window.connect(lambda: richieste.append(True))
            self.assertIsNone(porta_unica([], percorso))
            self.assertTrue(self._attendi(lambda: bool(richieste)))
            server.close()


if __name__ == "__main__":
    unittest.main()
