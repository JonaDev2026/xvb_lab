import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout
from ui.widgets import Ricerca, Cursore, Elenco, Finestrella, Tendina, Guida
from ui.main_window import MainWindow


class QtWidgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_main_window_module_imports(self):
        self.assertTrue(MainWindow)

    def test_main_window_constructs_without_libmpv(self):
        with patch("ui.main_window.MpvVideo", side_effect=RuntimeError("libmpv unavailable")):
            window = MainWindow()
            self.assertIsNone(window.player)
            window.close()
            self.app.processEvents()

    def test_fullscreen_overlay_reparents_and_restores_controls(self):
        with patch("ui.main_window.MpvVideo", side_effect=RuntimeError("libmpv unavailable")):
            window = MainWindow()
            window._attiva_overlay()
            self.assertIs(window.barra.parentWidget(), window.video)
            window._disattiva_overlay()
            self.assertIs(window.barra.parentWidget(), window._centrale)
            window.close()
            self.app.processEvents()

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

    def test_list_multi_delete_preserves_remaining_items(self):
        widget = Elenco(None)
        for iid in ("one", "two", "three", "four"):
            widget.insert("", "end", iid=iid, text=iid)
        widget.delete("one", "three")
        self.assertEqual(widget.get_children(), ("two", "four"))
        self.assertTrue(widget.exists("two"))
        self.assertTrue(widget.exists("four"))

    def test_list_keyboard_selection_tracks_current_row(self):
        widget = Elenco(None)
        widget.insert("", "end", iid="one", text="One")
        widget.insert("", "end", iid="two", text="Two")
        widget.setCurrentRow(1)
        self.assertEqual(widget.selection(), ("two",))

    def test_dialog_and_popup_construction(self):
        def corpo(parent):
            layout = QVBoxLayout(parent)
            layout.addWidget(QLabel("Body"))
        dialog = Finestrella(None, "Title", corpo)
        self.assertEqual(dialog.windowTitle(), "Title")
        self.assertGreater(dialog.sizeHint().height(), 0)
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
