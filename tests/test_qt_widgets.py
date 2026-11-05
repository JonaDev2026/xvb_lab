import json
import time
import hashlib
import os
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QPoint
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import QApplication, QLabel, QMenu, QVBoxLayout
from ui.widgets import Ricerca, Cursore, Elenco, Finestrella, Tendina, Guida
from ui.main_window import MainWindow, _AggiornaListe, _ScansionaCartelle, _prepara_file_cartella, _ScaricaCopertine


class QtWidgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_configured_imports_are_prepared_by_startup_worker(self):
        with tempfile.TemporaryDirectory() as root:
            percorso = os.path.join(root, "Imported Film (2022).mkv")
            with open(percorso, "wb") as stream:
                stream.write(b"video")
            preparati = [("Imported Film", percorso, None, "Video", root, "2022")]
            risultati = []
            with patch("ui.main_window.media_in", return_value=[]), patch("ui.main_window._prepara_file_cartella", return_value=preparati) as prepara:
                worker = _ScansionaCartelle([], {}, [percorso], ())
                worker.completato.connect(lambda dati, errore: risultati.append((dati, errore)))
                worker.run()
            self.assertEqual(risultati[0][1], "")
            self.assertEqual(risultati[0][0]["__importati__"], preparati)
            prepara.assert_called_once_with(
                root, [("Imported Film (2022)", percorso, None)], {}, [])

    def test_imported_audio_metadata_uses_configured_library_roots(self):
        percorso = "/media/imported/Artist/Album/Track.flac"
        with patch("ui.main_window.tag_di", return_value=("", "", "", "")), patch(
                "ui.main_window.dal_percorso",
                return_value=("Track", "Artist", "Album", "2020")) as dal:
            preparati = _prepara_file_cartella(
                "/media/imported/Artist/Album", [("Track", percorso, None)], {}, ["/media/library"])
        dal.assert_called_once_with(percorso, ["/media/library"])
        self.assertEqual(preparati[0][0], "Track")
        self.assertEqual(preparati[0][5], "Artist · Album · 2020")

    def test_imported_media_inside_configured_folder_are_not_prepared_twice(self):
        with tempfile.TemporaryDirectory() as root:
            percorso = os.path.join(root, "Film.mkv")
            with open(percorso, "wb") as stream:
                stream.write(b"video")
            elementi = [("Film", percorso, None)]
            preparati = [("Film", percorso, None, "Video", root, "")]
            risultati = []
            with patch("ui.main_window.media_in", return_value=elementi), patch("ui.main_window._prepara_file_cartella", return_value=preparati) as prepara:
                worker = _ScansionaCartelle([root], {}, [percorso], ())
                worker.completato.connect(lambda dati, errore: risultati.append((dati, errore)))
                worker.run()
            self.assertEqual(risultati[0][1], "")
            self.assertEqual(risultati[0][0][root], preparati)
            self.assertEqual(risultati[0][0]["__importati__"], [])
            prepara.assert_called_once()

    def test_startup_worker_results_add_imported_media_to_session(self):
        with patch("ui.main_window.MpvVideo", side_effect=RuntimeError("libmpv unavailable")):
            window = MainWindow()
            percorso = "/tmp/Imported Film.mkv"
            elemento = ("Imported Film", percorso, None, "Video", "/tmp", "2022")
            with patch.object(window, "_riempi_liste"), patch.object(window, "_riempi_elenco"):
                window._cartelle_configurate_scansionate({"__importati__": [elemento]}, "")
            self.assertIn(
                ("Imported Film", percorso, None, "Video", "__importati__"),
                window.sessione.canali)
            self.assertEqual(window.sottotitoli[percorso], "2022")
            window.close()
            self.app.processEvents()

    def test_video_menu_checkmarks_follow_saved_settings(self):
        with patch("ui.main_window.MpvVideo", side_effect=RuntimeError("libmpv unavailable")):
            window = MainWindow()
            self.assertTrue(window.azione_hwdec.isChecked())
            self.assertFalse(window.azione_deinterlaccia.isChecked())
            window.metti_proporzioni("16:9")
            self.assertTrue(window.azioni_proporzioni["16:9"].isChecked())
            self.assertFalse(window.azioni_proporzioni["-1"].isChecked())
            window.riempi()
            self.assertTrue(window.azione_riempi.isChecked())
            self.assertFalse(window.azioni_proporzioni["16:9"].isChecked())
            window.deinterlaccia()
            self.assertTrue(window.azione_deinterlaccia.isChecked())
            window.decodifica_hw()
            self.assertFalse(window.azione_hwdec.isChecked())
            window.close()
            self.app.processEvents()

    def test_playback_and_audio_menu_states_follow_current_settings(self):
        with patch("ui.main_window.MpvVideo", side_effect=RuntimeError("libmpv unavailable")):
            window = MainWindow()
            self.assertTrue(window.azioni_velocita[1].isChecked())
            self.assertFalse(window.azione_carica_sottotitoli.isEnabled())
            self.assertFalse(window.azione_sottotitoli_online.isEnabled())
            window.metti_velocita(1.5)
            window.mpris_shuffle(True)
            window.metti_ripeti("uno")
            window.boost()
            window.normalizza()
            window._aggiorna_menu_playback()
            window._aggiorna_menu_audio()
            self.assertTrue(window.azioni_velocita[1.5].isChecked())
            self.assertTrue(window.azione_shuffle.isChecked())
            self.assertTrue(window.azioni_ripeti["uno"].isChecked())
            self.assertTrue(window.azione_boost.isChecked())
            self.assertTrue(window.azione_normalizza.isChecked())
            self.assertFalse(window.azione_carica_sottotitoli.isEnabled())
            window.file_in_onda = "/tmp/movie.mkv"
            window._aggiorna_menu_audio()
            self.assertTrue(window.azione_carica_sottotitoli.isEnabled())
            self.assertTrue(window.azione_sottotitoli_online.isEnabled())
            window.close()
            self.app.processEvents()

    def test_iptv_context_menu_restores_stable_actions(self):
        with patch("ui.main_window.MpvVideo", side_effect=RuntimeError("libmpv unavailable")):
            window = MainWindow()
            url = "https://example.test/context-menu"
            window._canali_visibili = [("News", url, "news", "World", "playlist.m3u")]
            window.elenco.insert("", "end", iid="0", text="News")
            item = window.elenco.topLevelItem(0)
            viste = []
            with patch.object(window.elenco, "itemAt", return_value=item), \
                    patch.object(window.elenco, "row", return_value=0), \
                    patch.object(QMenu, "exec", autospec=True,
                                 side_effect=lambda menu, _pos: viste.extend(
                                     action.text() for action in menu.actions())):
                window._menu_canale(QPoint(2, 2))
            self.assertIn("Rename...", viste)
            self.assertIn("Set logo...", viste)
            self.assertIn("Set color...", viste)
            self.assertIn("Add to favorites", viste)
            window.close()
            self.app.processEvents()

    def test_local_media_context_menu_keeps_cover_and_favorite_actions(self):
        with patch("ui.main_window.MpvVideo", side_effect=RuntimeError("libmpv unavailable")):
            window = MainWindow()
            percorso = "/tmp/context-menu-track.mp3"
            window._canali_visibili = [("Track", percorso, None, "Music", "__importati__")]
            window.elenco.insert("", "end", iid="0", text="Track")
            item = window.elenco.topLevelItem(0)
            viste = []
            with patch.object(window.elenco, "itemAt", return_value=item), \
                    patch.object(window.elenco, "row", return_value=0), \
                    patch.object(QMenu, "exec", autospec=True,
                                 side_effect=lambda menu, _pos: viste.extend(
                                     action.text() for action in menu.actions())):
                window._menu_canale(QPoint(2, 2))
            self.assertIn("Set cover...", viste)
            self.assertIn("Add to favorites", viste)
            self.assertNotIn("Rename...", viste)
            window.close()
            self.app.processEvents()

    def test_channel_rename_is_saved_and_used_for_display_only(self):
        with patch("ui.main_window.MpvVideo", side_effect=RuntimeError("libmpv unavailable")):
            window = MainWindow()
            url = "https://example.test/renamed-channel"
            with patch("ui.main_window.QInputDialog.getText", return_value=("My News", True)), \
                    patch("ui.main_window.scrivi_config"), \
                    patch.object(window, "_riempi_elenco"):
                window.rinomina_canale("News", url)
            self.assertEqual(window.sessione.config["nomi_canali"][url], "My News")
            self.assertEqual(window.nome_canale("News", url), "My News")
            with patch("ui.main_window.QInputDialog.getText", return_value=("News", True)), \
                    patch("ui.main_window.scrivi_config"), \
                    patch.object(window, "_riempi_elenco"):
                window.rinomina_canale("News", url)
            self.assertNotIn(url, window.sessione.config["nomi_canali"])
            self.assertEqual(window.nome_canale("News", url), "News")
            window.close()
            self.app.processEvents()

    def test_manual_channel_color_updates_config_and_list(self):
        from PySide6.QtGui import QColor
        with patch("ui.main_window.MpvVideo", side_effect=RuntimeError("libmpv unavailable")):
            window = MainWindow()
            url = "https://example.test/colored-channel"
            with patch("ui.main_window.QColorDialog.getColor", return_value=QColor("#123456")), \
                    patch("ui.main_window.scrivi_config"), \
                    patch.object(window, "_riempi_elenco") as refill:
                window.scegli_colore("News", url)
            self.assertEqual(window.sessione.config["colori_canali"][url], "#123456")
            refill.assert_called_once()
            self.assertEqual(window.colore_canale("News", url), "#123456")
            with patch("ui.main_window.scrivi_config"), patch.object(window, "_riempi_elenco") as refill:
                window.togli_colore(url)
            self.assertNotIn(url, window.sessione.config["colori_canali"])
            refill.assert_called_once()
            window.close()
            self.app.processEvents()

    def test_renamed_channel_uses_alias_in_status_without_changing_epg_name(self):
        with patch("ui.main_window.MpvVideo", side_effect=RuntimeError("libmpv unavailable")):
            window = MainWindow()
            url = "https://example.test/status-name"
            window.sessione.config.setdefault("nomi_canali", {})[url] = "My News"
            window.file_in_onda = url
            window.nome_in_onda = "News"
            window.ide_in_onda = "news"
            window.aggiorna_info_canale()
            self.assertEqual(window.riga_stato.text(), "My News")
            self.assertEqual(window._programmi_canale(), [])
            self.assertEqual(window.nome_in_onda, "News")
            window.close()
            self.app.processEvents()

    def test_epg_sidebar_context_menu_restores_rename_and_remove(self):
        with patch("ui.main_window.MpvVideo", side_effect=RuntimeError("libmpv unavailable")):
            window = MainWindow()
            url = "https://example.test/guide.xml"
            window.sessione.config["epg"] = [url]
            window._riempi_liste()
            item = window.el_liste.item_by_id("epg:0")
            viste = []
            with patch.object(window.el_liste, "itemAt", return_value=item), \
                    patch.object(QMenu, "exec", autospec=True,
                                 side_effect=lambda menu, _pos: viste.extend(
                                     action.text() for action in menu.actions())):
                window._menu_liste(QPoint(2, 2))
            self.assertIn("Rename...", viste)
            self.assertIn("Remove guide", viste)
            window.close()
            self.app.processEvents()

    def test_epg_rename_is_persisted_and_reflected_in_sidebar(self):
        with patch("ui.main_window.MpvVideo", side_effect=RuntimeError("libmpv unavailable")):
            window = MainWindow()
            url = "https://example.test/renamed-guide.xml"
            window.sessione.config["epg"] = [url]
            with patch.object(window, "_chiedi_testo", return_value="My Guide"), \
                    patch("ui.main_window.scrivi_config"), \
                    patch.object(window, "_riempi_liste") as refill:
                window.rinomina_guida(url)
            self.assertEqual(window.sessione.config["epg_nomi_utente"][url], "My Guide")
            self.assertEqual(window.nome_guida(url), "My Guide")
            refill.assert_called_once()
            window.close()
            self.app.processEvents()

    def test_local_media_cover_uses_adjacent_jpeg_and_remote_cover_cache(self):
        with patch("ui.main_window.MpvVideo", side_effect=RuntimeError("libmpv unavailable")):
            window = MainWindow()
            self.assertEqual(
                window.percorso_copertina("/media/video/Movie.mkv"),
                "/media/video/Movie.jpg")
            remoto = window.percorso_copertina("https://example.test/channel")
            self.assertTrue(remoto.endswith(".jpg"))
            self.assertNotEqual(remoto, "https://example.test/channel")
            window.close()
            self.app.processEvents()

    def test_local_media_cover_is_saved_as_jpeg_and_used_by_list(self):
        with tempfile.TemporaryDirectory() as root, \
                patch("ui.main_window.MpvVideo", side_effect=RuntimeError("libmpv unavailable")):
            window = MainWindow()
            media = os.path.join(root, "Track.mp3")
            sorgente = os.path.join(root, "cover.png")
            with open(media, "wb") as stream:
                stream.write(b"audio")
            immagine = QPixmap(16, 16)
            immagine.fill(QColor("#123456"))
            self.assertTrue(immagine.save(sorgente, "PNG"))
            with patch("ui.main_window.QFileDialog.getOpenFileName",
                       return_value=(sorgente, "")), patch.object(window, "_riempi_elenco"):
                window.metti_copertina(media)
            destinazione = os.path.join(root, "Track.jpg")
            self.assertTrue(os.path.isfile(destinazione))
            self.assertFalse(QPixmap(destinazione).isNull())
            self.assertFalse(window.logo_di(media).isNull())
            window.close()
            self.app.processEvents()

    def test_saved_and_temporary_urls_are_restored_in_sidebar(self):
        with patch("ui.main_window.MpvVideo", side_effect=RuntimeError("libmpv unavailable")):
            window = MainWindow()
            radio = "https://example.test/radio"
            podcast = "https://example.test/podcast"
            temporary = "https://example.test/live"
            window.sessione.config["url_salvati"] = {
                "radio": [radio],
                "podcast": [podcast],
            }
            window.sessione.config["url_aperti"] = [temporary]
            window.sessione.config.setdefault("nomi_url", {})[radio] = "My Radio"
            window._riempi_liste()
            self.assertTrue(window.el_liste.exists("url"))
            self.assertEqual(window.el_liste.item("urlcat:radio", "valore"),
                             ("__url_cat__", "radio"))
            self.assertEqual(window.el_liste.item("urlcat:radio:0", "valore"),
                             ("__url__", radio))
            self.assertEqual(window.el_liste.item("urlcat:radio:0", "text"), " My Radio")
            self.assertEqual(window.el_liste.item("urlcat:temporary", "valore"),
                             ("__url_cat__", None))
            self.assertEqual(window.el_liste.item("urlcat:temporary:0", "valore"),
                             ("__url__", temporary))
            window.close()
            self.app.processEvents()

    def test_url_sidebar_categories_filter_and_open_the_selected_url(self):
        with patch("ui.main_window.MpvVideo", side_effect=RuntimeError("libmpv unavailable")):
            window = MainWindow()
            radio = "https://example.test/radio"
            temporary = "https://example.test/live"
            window.sessione.config["url_salvati"] = {"radio": [radio]}
            window.sessione.config["url_aperti"] = [temporary]
            window._riempi_liste()
            window._scegli_voce_liste("urlcat:radio")
            self.assertEqual(window._percorso_attivo, "__url__")
            self.assertEqual(window._categoria_attiva, "radio")
            self.assertEqual([voce[1] for voce in window._canali_visibili], [radio])
            with patch.object(window, "apri_url_da") as apri:
                window._scegli_voce_liste("urlcat:radio:0")
                apri.assert_called_once_with(radio)
            self.assertEqual(window._categoria_attiva, "radio")
            window._scegli_voce_liste("url")
            self.assertEqual(window._categoria_attiva, None)
            self.assertEqual([voce[1] for voce in window._canali_visibili], [temporary])
            with patch.object(window, "apri_url_da") as apri:
                window._scegli_voce_liste("urlcat:temporary:0")
                apri.assert_called_once_with(temporary)
            self.assertEqual(window._categoria_attiva, None)
            window.close()
            self.app.processEvents()

    def test_url_rename_can_be_reset_to_derived_name(self):
        with patch("ui.main_window.MpvVideo", side_effect=RuntimeError("libmpv unavailable")):
            window = MainWindow()
            url = "https://example.test/old-name.m3u8"
            window.sessione.config.setdefault("nomi_url", {})[url] = "Old name"
            with patch.object(window, "_chiedi_testo", return_value=""), \
                    patch("ui.main_window.scrivi_config"), \
                    patch.object(window, "_riempi_liste"), \
                    patch.object(window, "_riempi_elenco"):
                window.rinomina_url(url)
            self.assertNotIn(url, window.sessione.config["nomi_url"])
            self.assertNotEqual(window.nome_di_url(url), "Old name")
            window.close()
            self.app.processEvents()

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
    def test_playback_menu_restores_track_and_chapter_navigation(self):
        with patch("ui.main_window.MpvVideo", side_effect=RuntimeError("libmpv unavailable")):
            window = MainWindow()
            self.assertFalse(window.azione_capitolo_precedente.isVisible())
            self.assertFalse(window.azione_capitolo_successivo.isVisible())
            self.assertFalse(window.menu_capitoli.menuAction().isVisible())

            class Player:
                def leggi_nodo(self, nome):
                    return [{"title": "Opening", "time": 0},
                            {"title": "Main", "time": 60}]
                def leggi(self, nome):
                    return 0

            window.player = Player()
            window._aggiorna_visibilita_capitoli()
            self.assertTrue(window.azione_capitolo_precedente.isVisible())
            self.assertTrue(window.azione_capitolo_successivo.isVisible())
            self.assertTrue(window.menu_capitoli.menuAction().isVisible())
            window._riempi_menu_capitoli()
            self.assertEqual(window.menu_capitoli.actions()[0].text(),
                             "✓  Opening  ·  00:00:00")
            self.assertEqual(window.menu_capitoli.actions()[1].text(),
                             "    Main  ·  00:01:00")
            window.player = None
            window.close()
            self.app.processEvents()

    def test_bulk_artwork_worker_downloads_movie_poster_and_persists_metadata(self):
        with tempfile.TemporaryDirectory() as root:
            film = os.path.join(root, "Film (2020).mkv")
            with open(film, "wb") as stream:
                stream.write(b"video")
            info_file = os.path.join(root, "info.json")
            tried_file = os.path.join(root, "tried.json")
            scaricati = []

            def scarica(_url, destinazione):
                with open(destinazione, "wb") as stream:
                    stream.write(b"image")
                scaricati.append(destinazione)

            with patch("ui.main_window.FILE_INFO", info_file), \
                 patch("ui.main_window.FILE_PROVATI", tried_file), \
                 patch("ui.main_window.TMDB_CHIAVE", "test-key"), \
                 patch("ui.main_window.info_tmdb", return_value={
                     "poster": "https://example.test/poster.jpg", "generi": ["18"]}), \
                 patch("ui.main_window.generi_tmdb", return_value={"18": "Drama"}), \
                 patch("ui.main_window.scarica_in", side_effect=scarica):
                worker = _ScaricaCopertine([film], root, False, {}, {}, [])
                worker.run()

            poster = os.path.join(root, "Film (2020).jpg")
            self.assertTrue(os.path.isfile(poster))
            self.assertEqual(scaricati, [poster])
            self.assertEqual((worker.fatti, worker.nuove), (1, 1))
            self.assertEqual(worker.info[film]["generi"], ["Drama"])
            with open(info_file, encoding="utf-8") as stream:
                self.assertEqual(json.load(stream)[film]["generi"], ["Drama"])
            with open(tried_file, encoding="utf-8") as stream:
                self.assertIn(film, json.load(stream))

    def test_status_bar_shows_active_iptv_category_only(self):
        with patch("ui.main_window.MpvVideo", side_effect=RuntimeError("libmpv unavailable")):
            window = MainWindow()
            url = "https://example.test/news"
            window.sessione.canali = [("News", url, "news", "World", "playlist.m3u")]
            window._imposta_categoria_attiva(url)
            self.assertEqual(window.et_categoria.text(), "World")
            self.assertFalse(window.et_categoria.isHidden())
            window._imposta_categoria_attiva("/media/song.flac")
            self.assertTrue(window.et_categoria.isHidden())
            self.assertIsNone(window._categoria_attiva)
            window.close()
            self.app.processEvents()

    def test_status_bar_shows_current_and_next_epg_program(self):
        with patch("ui.main_window.MpvVideo", side_effect=RuntimeError("libmpv unavailable")), \
             patch("ui.main_window.time.time", return_value=150):
            window = MainWindow()
            window.nome_in_onda = "News"
            window.ide_in_onda = "news"
            window.file_in_onda = "https://example.test/news"
            window.sessione.epg = {"news": [
                (100, 200, "Current bulletin"),
                (200, 300, "Evening report"),
            ]}
            window.sessione.epg_nomi = {}
            window.aggiorna_info_canale()
            self.assertEqual(window.riga_stato.text(), "News  ·  Current bulletin")
            self.assertEqual(window.et_ora_programma.text(),
                             "%s–%s" % (time.strftime("%H:%M", time.localtime(100)),
                                        time.strftime("%H:%M", time.localtime(200))))
            self.assertEqual(window.et_prossimo.text(), "Next: Evening report")
            self.assertFalse(window.et_prossimo.isHidden())
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
    def test_external_playlist_is_selected_after_reload(self):
        with patch("ui.main_window.MpvVideo", side_effect=RuntimeError("libmpv unavailable")):
            window = MainWindow()
            with tempfile.NamedTemporaryFile(suffix=".m3u") as stream:
                with patch("ui.main_window.e_una_lista", return_value=True), \
                     patch("ui.main_window.scrivi_config"), \
                     patch.object(window, "ricarica_liste") as ricarica, \
                     patch.object(window, "_completa_apri_da_fuori"):
                    window.apri_da_fuori([stream.name])
                ricarica.assert_called_once_with(scegli=os.path.abspath(stream.name), forza=False)
            window.close()
            self.app.processEvents()
    def test_tv_guide_window_is_single_instance(self):
        with patch("ui.main_window.MpvVideo", side_effect=RuntimeError("libmpv unavailable")):
            window = MainWindow()
            window.epg = {"news": []}
            window.sessione.epg = window.epg
            window.apri_guida()
            prima = window._finestra_guida
            window.apri_guida()
            self.assertIs(window._finestra_guida, prima)
            prima.close()
            self.app.processEvents()
            self.assertIsNone(window._finestra_guida)
            window.apri_guida()
            self.assertIsNotNone(window._finestra_guida)
            window.close()
            self.app.processEvents()
    def test_removed_epg_reports_its_saved_name(self):
        with patch("ui.main_window.MpvVideo", side_effect=RuntimeError("libmpv unavailable")):
            window = MainWindow()
            url = "https://example.test/guide.xml.gz"
            window.sessione.config["epg"] = [url]
            window.sessione.config["epg_nomi"] = {url: "xmltv-original.xml"}
            with patch("ui.main_window.scrivi_config"), \
                 patch.object(window, "ricarica_guida"), \
                 patch.object(window, "_riempi_liste"):
                window.togli_epg(url)
            self.assertIn("xmltv-original.xml", window.riga_stato.text())
            window.close()
            self.app.processEvents()
    def test_playlist_refresh_does_not_reload_unchanged_content(self):
        with tempfile.TemporaryDirectory() as root:
            url = "https://example.test/list.m3u"
            cache = os.path.join(root, hashlib.md5(url.encode()).hexdigest() + ".m3u")
            with open(cache, "wb") as stream:
                stream.write(b"#EXTM3U\n#EXTINF:-1,News\\nhttps://stream.test/news")
            risultati = []
            def aggiorna(_url):
                os.utime(cache, (2000, 2000))
                return cache
            with patch("ui.main_window.CACHE_LISTE", root), \
                 patch("ui.main_window.copia_lista_url", side_effect=aggiorna):
                worker = _AggiornaListe([url])
                worker.completato.connect(risultati.append)
                worker.run()
            self.assertEqual(risultati, [False])

    def test_playlist_refresh_reloads_changed_content(self):
        with tempfile.TemporaryDirectory() as root:
            url = "https://example.test/list.m3u"
            cache = os.path.join(root, hashlib.md5(url.encode()).hexdigest() + ".m3u")
            with open(cache, "wb") as stream:
                stream.write(b"#EXTM3U\\n#EXTINF:-1,News\\nhttps://stream.test/news")
            risultati = []
            def aggiorna(_url):
                with open(cache, "wb") as stream:
                    stream.write(b"#EXTM3U\\n#EXTINF:-1,Sports\\nhttps://stream.test/sports")
                return cache
            with patch("ui.main_window.CACHE_LISTE", root), \
                 patch("ui.main_window.copia_lista_url", side_effect=aggiorna):
                worker = _AggiornaListe([url])
                worker.completato.connect(risultati.append)
                worker.run()
            self.assertEqual(risultati, [True])
    def test_record_button_allows_unencrypted_dvd(self):
        with patch("ui.main_window.MpvVideo", side_effect=RuntimeError("libmpv unavailable")):
            window = MainWindow()
            window.file_in_onda = "dvd:///media/dvd"
            window.nome_in_onda = "DVD Movie"
            with patch("ui.main_window.dvd_cifrato", return_value=False), \
                 patch.object(window, "avvia_registrazione") as avvia:
                window.registra()
            avvia.assert_called_once_with("DVD Movie", 0.0)
            window.close()
            self.app.processEvents()

    def test_record_button_rejects_encrypted_dvd(self):
        with patch("ui.main_window.MpvVideo", side_effect=RuntimeError("libmpv unavailable")):
            window = MainWindow()
            window.file_in_onda = "dvd:///media/dvd"
            window.nome_in_onda = "Protected DVD"
            with patch("ui.main_window.dvd_cifrato", return_value=True), \
                 patch.object(window, "avvia_registrazione") as avvia:
                window.registra()
            avvia.assert_not_called()
            window.close()
            self.app.processEvents()
    def test_record_button_switches_to_stop_while_recording(self):
        with patch("ui.main_window.MpvVideo", side_effect=RuntimeError("libmpv unavailable")):
            window = MainWindow()
            pulsante = window._pulsanti["rec"]
            originale = pulsante.toolTip()
            window._imposta_pulsante_rec(True)
            attiva = pulsante.toolTip()
            self.assertNotEqual(attiva, originale)
            window._imposta_pulsante_rec(False)
            self.assertEqual(pulsante.toolTip(), originale)
            window.close()
            self.app.processEvents()

    def test_status_bar_shows_active_iptv_category_only(self):
        with patch("ui.main_window.MpvVideo", side_effect=RuntimeError("libmpv unavailable")):
            window = MainWindow()
            url = "https://example.test/news"
            window.sessione.canali = [("News", url, "news", "World", "playlist.m3u")]
            window._imposta_categoria_attiva(url)
            self.assertEqual(window.et_categoria.text(), "World")
            self.assertFalse(window.et_categoria.isHidden())
            window._imposta_categoria_attiva("/media/song.flac")
            self.assertTrue(window.et_categoria.isHidden())
            self.assertIsNone(window._categoria_attiva)
            window.close()
            self.app.processEvents()

    def test_status_bar_shows_current_and_next_epg_program(self):
        with patch("ui.main_window.MpvVideo", side_effect=RuntimeError("libmpv unavailable")), \
             patch("ui.main_window.time.time", return_value=150):
            window = MainWindow()
            window.nome_in_onda = "News"
            window.ide_in_onda = "news"
            window.file_in_onda = "https://example.test/news"
            window.sessione.epg = {"news": [
                (100, 200, "Current bulletin"),
                (200, 300, "Evening report"),
            ]}
            window.sessione.epg_nomi = {}
            window.aggiorna_info_canale()
            self.assertEqual(window.riga_stato.text(), "News  ·  Current bulletin")
            self.assertEqual(window.et_ora_programma.text(),
                             "%s–%s" % (time.strftime("%H:%M", time.localtime(100)),
                                        time.strftime("%H:%M", time.localtime(200))))
            self.assertEqual(window.et_prossimo.text(), "Next: Evening report")
            self.assertFalse(window.et_prossimo.isHidden())
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
    def test_external_playlist_is_selected_after_reload(self):
        with patch("ui.main_window.MpvVideo", side_effect=RuntimeError("libmpv unavailable")):
            window = MainWindow()
            with tempfile.NamedTemporaryFile(suffix=".m3u") as stream:
                with patch("ui.main_window.e_una_lista", return_value=True), \
                     patch("ui.main_window.scrivi_config"), \
                     patch.object(window, "ricarica_liste") as ricarica, \
                     patch.object(window, "_completa_apri_da_fuori"):
                    window.apri_da_fuori([stream.name])
                ricarica.assert_called_once_with(scegli=os.path.abspath(stream.name), forza=False)
            window.close()
            self.app.processEvents()
    def test_tv_guide_window_is_single_instance(self):
        with patch("ui.main_window.MpvVideo", side_effect=RuntimeError("libmpv unavailable")):
            window = MainWindow()
            window.epg = {"news": []}
            window.sessione.epg = window.epg
            window.apri_guida()
            prima = window._finestra_guida
            window.apri_guida()
            self.assertIs(window._finestra_guida, prima)
            prima.close()
            self.app.processEvents()
            self.assertIsNone(window._finestra_guida)
            window.apri_guida()
            self.assertIsNotNone(window._finestra_guida)
            window.close()
            self.app.processEvents()
    def test_removed_epg_reports_its_saved_name(self):
        with patch("ui.main_window.MpvVideo", side_effect=RuntimeError("libmpv unavailable")):
            window = MainWindow()
            url = "https://example.test/guide.xml.gz"
            window.sessione.config["epg"] = [url]
            window.sessione.config["epg_nomi"] = {url: "xmltv-original.xml"}
            with patch("ui.main_window.scrivi_config"), \
                 patch.object(window, "ricarica_guida"), \
                 patch.object(window, "_riempi_liste"):
                window.togli_epg(url)
            self.assertIn("xmltv-original.xml", window.riga_stato.text())
            window.close()
            self.app.processEvents()
    def test_playlist_refresh_does_not_reload_unchanged_content(self):
        with tempfile.TemporaryDirectory() as root:
            url = "https://example.test/list.m3u"
            cache = os.path.join(root, hashlib.md5(url.encode()).hexdigest() + ".m3u")
            with open(cache, "wb") as stream:
                stream.write(b"#EXTM3U\n#EXTINF:-1,News\\nhttps://stream.test/news")
            risultati = []
            def aggiorna(_url):
                os.utime(cache, (2000, 2000))
                return cache
            with patch("ui.main_window.CACHE_LISTE", root), \
                 patch("ui.main_window.copia_lista_url", side_effect=aggiorna):
                worker = _AggiornaListe([url])
                worker.completato.connect(risultati.append)
                worker.run()
            self.assertEqual(risultati, [False])

    def test_playlist_refresh_reloads_changed_content(self):
        with tempfile.TemporaryDirectory() as root:
            url = "https://example.test/list.m3u"
            cache = os.path.join(root, hashlib.md5(url.encode()).hexdigest() + ".m3u")
            with open(cache, "wb") as stream:
                stream.write(b"#EXTM3U\\n#EXTINF:-1,News\\nhttps://stream.test/news")
            risultati = []
            def aggiorna(_url):
                with open(cache, "wb") as stream:
                    stream.write(b"#EXTM3U\\n#EXTINF:-1,Sports\\nhttps://stream.test/sports")
                return cache
            with patch("ui.main_window.CACHE_LISTE", root), \
                 patch("ui.main_window.copia_lista_url", side_effect=aggiorna):
                worker = _AggiornaListe([url])
                worker.completato.connect(risultati.append)
                worker.run()
            self.assertEqual(risultati, [True])
    def test_record_button_allows_unencrypted_dvd(self):
        with patch("ui.main_window.MpvVideo", side_effect=RuntimeError("libmpv unavailable")):
            window = MainWindow()
            window.file_in_onda = "dvd:///media/dvd"
            window.nome_in_onda = "DVD Movie"
            with patch("ui.main_window.dvd_cifrato", return_value=False), \
                 patch.object(window, "avvia_registrazione") as avvia:
                window.registra()
            avvia.assert_called_once_with("DVD Movie", 0.0)
            window.close()
            self.app.processEvents()

    def test_record_button_rejects_encrypted_dvd(self):
        with patch("ui.main_window.MpvVideo", side_effect=RuntimeError("libmpv unavailable")):
            window = MainWindow()
            window.file_in_onda = "dvd:///media/dvd"
            window.nome_in_onda = "Protected DVD"
            with patch("ui.main_window.dvd_cifrato", return_value=True), \
                 patch.object(window, "avvia_registrazione") as avvia:
                window.registra()
            avvia.assert_not_called()
            window.close()
            self.app.processEvents()
    def test_record_button_switches_to_stop_while_recording(self):
        with patch("ui.main_window.MpvVideo", side_effect=RuntimeError("libmpv unavailable")):
            window = MainWindow()
            pulsante = window._pulsanti["rec"]
            originale = pulsante.toolTip()
            window._imposta_pulsante_rec(True)
            attiva = pulsante.toolTip()
            self.assertNotEqual(attiva, originale)
            window._imposta_pulsante_rec(False)
            self.assertEqual(pulsante.toolTip(), originale)
            window.close()
            self.app.processEvents()

if __name__ == "__main__":
    unittest.main()
