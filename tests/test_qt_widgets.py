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
            self.assertEqual(window.nome_in_onda, "")
            self.assertIsNone(window.ide_in_onda)
            self.assertIsNone(window.file_in_onda)
            self.assertEqual(window._durate_cercate, set())
            self.assertEqual(window._registrazioni_attive, [])
            self.assertEqual(window._layout_principale.indexOf(window.avviso), 1)
            self.assertIs(window.barra.parentWidget(), window.video)
            self.assertTrue(window._overlay_attivo)
            window.close()
            self.app.processEvents()

    def test_fullscreen_overlay_reparents_and_restores_controls(self):
        with patch("ui.main_window.MpvVideo", side_effect=RuntimeError("libmpv unavailable")):
            window = MainWindow()
            window._attiva_overlay()
            self.assertIs(window.barra.parentWidget(), window.video)
            window._disattiva_overlay()
            self.assertIs(window.barra.parentWidget(), window._centrale)
            self.assertEqual(window._layout_principale.indexOf(window.barra), 2)
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

    def test_on_air_list_item_keeps_highlight_without_selection(self):
        widget = Elenco(None)
        widget.insert("", "end", iid="on-air", text="Channel", tags=("onda",))
        widget.selection_set("on-air")
        self.assertEqual(widget.selection(), ())

    def test_dialog_and_popup_construction(self):
        def corpo(parent):
            parent.contenuto.addWidget(QLabel("Body"))
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

    def test_recording_group_shows_its_files_in_main_list(self):
        with patch("ui.main_window.MpvVideo", side_effect=RuntimeError("libmpv unavailable")):
            window = MainWindow()
            path = "/tmp/News/Evening News.mkv"
            raccolte = [(("News", "2026-11-05"), [("20:30", "Evening News", path)])]
            with patch("ui.main_window.registrazioni", return_value=raccolte), \
                 patch.object(window, "logo_di", return_value=None), \
                 patch.object(window, "colore_canale", return_value="#ffffff"):
                window._riempi_liste()
                self.assertEqual(window.el_liste.item("registrazioni:0", "valore"),
                                 ("__recordings_group__", ("News", "2026-11-05")))
                window._scegli_voce_liste("registrazioni:0")
                self.assertEqual(window._canali_visibili,
                                 [("Evening News", path, None, "20:30", "__recordings__")])
            window.close()
            self.app.processEvents()
    def test_local_progress_requests_missing_duration_asynchronously(self):
        with patch("ui.main_window.MpvVideo", side_effect=RuntimeError("libmpv unavailable")):
            window = MainWindow()
            path = "/tmp/recording.mkv"
            window._canali_visibili = [("Recording", path, None, "20:30", "__recordings__")]
            window.sessione.config.setdefault("posizioni", {})[path] = 15.0
            window.sessione.config.setdefault("durate", {}).pop(path, None)
            with patch.object(window, "cerca_durata") as cerca:
                self.assertIsNone(window._progresso_di("0"))
                cerca.assert_called_once_with(path)
            window.close()
            self.app.processEvents()
    def test_mpris_metadata_timer_runs_only_when_service_is_available(self):
        class Servizio:
            def __init__(self):
                self.stato = None
            def aggiorna(self, stato):
                self.stato = stato
        servizio = Servizio()
        with patch("ui.main_window.MpvVideo", side_effect=RuntimeError("libmpv unavailable")), \
             patch("ui.main_window.avvia_mpris", return_value=servizio):
            window = MainWindow()
            self.assertTrue(window._timer_mpris.isActive())
            self.assertEqual(window._timer_mpris.interval(), 1000)
            window._aggiorna_mpris()
            self.assertEqual(servizio.stato["stato"], "Stopped")
            window.close()
            self.assertFalse(window._timer_mpris.isActive())
            self.app.processEvents()
    def test_temporary_urls_are_removed_from_config_on_exit(self):
        with patch("ui.main_window.MpvVideo", side_effect=RuntimeError("libmpv unavailable")):
            window = MainWindow()
            temporaneo = "https://example.test/live.m3u8"
            salvato = "https://example.test/saved.m3u8"
            window.sessione.config["url_aperti"] = [temporaneo]
            window.sessione.config["nomi_url"] = {temporaneo: "Temporary", salvato: "Saved"}
            with patch("ui.main_window.copertina_url", return_value="/tmp/temp-cover.jpg"), \
                 patch("ui.main_window.os.remove") as rimuovi:
                window._via_url_temporanei()
                rimuovi.assert_called_once_with("/tmp/temp-cover.jpg")
            self.assertEqual(window.sessione.config["url_aperti"], [])
            self.assertEqual(window.sessione.config["nomi_url"], {salvato: "Saved"})
            window.close()
            self.app.processEvents()

if __name__ == "__main__":
    unittest.main()
