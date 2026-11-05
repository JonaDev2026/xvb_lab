import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLabel
from ui.widgets import Ricerca, Cursore, Elenco, Finestrella, Tendina, Guida
from ui.main_window import MainWindow


class QtWidgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_main_window_module_imports(self):
        self.assertTrue(MainWindow)

    def test_search_callback_and_value(self):
        calls = []
        widget = Ricerca(None, lambda: calls.append(True))
        widget.casella.setText("news")
        self.assertEqual(widget.get(), "news")
        self.assertTrue(calls)

    def test_slider_callback_and_bounds(self):
        calls = []
        widget = Cursore(None, calls.append)
        widget.set(140)
        self.assertEqual(widget.get(), 100)
        self.assertEqual(calls, [100])

    def test_list_treeview_compatibility(self):
        widget = Elenco(None)
        iid = widget.insert("", "end", iid="channel-1", text="Channel\nNews")
        self.assertEqual(iid, "channel-1")
        self.assertTrue(widget.exists(iid))
        self.assertEqual(widget.item(iid, "text"), "Channel\nNews")
        widget.selection_set(iid)
        self.assertEqual(widget.selection(), (iid,))
        widget.delete(iid)
        self.assertFalse(widget.exists(iid))

    def test_dialog_and_popup_construction(self):
        dialog = Finestrella(None, "Title", lambda parent: parent.layout().addWidget(QLabel("Body")))
        self.assertEqual(dialog.windowTitle(), "Title")
        popup = Tendina(None)
        self.assertFalse(popup.aperta())

    def test_guide_empty_playlist(self):
        class App:
            root = None
            canali = []
            epg = {}
            epg_nomi = {}
        guide = Guida(App())
        self.assertEqual(guide.righe, [])
        guide.close()


if __name__ == "__main__":
    unittest.main()
