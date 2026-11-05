from PySide6.QtCore import Qt, QUrl, QThread, Signal, QTimer
from PySide6.QtGui import QAction, QKeySequence, QIcon, QDesktopServices, QPixmap
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QDialog,
    QPushButton, QFileDialog, QInputDialog, QMessageBox, QSlider, QTreeWidget, QTreeWidgetItem
)
from engine.mpv import MpvVideo
from ui.widgets import Elenco, Ricerca, Guida
from ui.sidebar import Sidebar
from core.session import Sessione
from core.media import media_in, AUDIO
from core.tags import leggi_tag, tag_di, scrivi_tag
from core.metadata import titolo_anno, dal_percorso, copertina_url, copertina_dentro, poster_film
from integrations.mpris import avvia_mpris
from core.config import scrivi_config, CARTELLE_LISTE, REGISTRAZIONI, leggi_config
from i18n import _, imposta_lingua, LINGUE
from core.playlists import liste_in_cartella, BUFFER, LOGHI
from core.colors import CACHE_LOGHI, leggi_colori, scrivi_colori, colore_di, colore_dal_logo
from core.constants import SCALA_FILE
import os
import re
import time
import random
import json


class _CaricaGuide(QThread):
    completato = Signal()
    errore = Signal(str)

    def __init__(self, sessione):
        super().__init__()
        self.sessione = sessione

    def run(self):
        try:
            self.sessione.carica_guide()
        except Exception as errore:
            self.errore.emit(str(errore))
        self.completato.emit()



class _ScaricaColoreLogo(QThread):
    completato = Signal(str, str)

    def __init__(self, url, logo):
        super().__init__()
        self.url = url
        self.logo = logo

    def run(self):
        try:
            colore = colore_dal_logo(self.logo) or ""
        except Exception:
            colore = ""
        self.completato.emit(self.url, colore)



class _CaricaCopertina(QThread):
    completato = Signal(str)

    def __init__(self, url, destinazione):
        super().__init__()
        self.url = url
        self.destinazione = destinazione

    def run(self):
        try:
            dati = copertina_dentro(self.url)
            if dati:
                os.makedirs(os.path.dirname(self.destinazione), exist_ok=True)
                with open(self.destinazione, "wb") as stream:
                    stream.write(dati)
        except Exception:
            pass
        self.completato.emit(self.url)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        imposta_lingua(leggi_config().get("lingua", "en"))
        self.setWindowTitle("XVB v4.4.4")
        self.resize(1280, 720)
        self.setMinimumSize(800, 480)
        self.setStyleSheet(
            "QMainWindow,QWidget{background:#1c1b22;color:#e0e0e0}"
            "QMenuBar{background:#1c1b22;color:white}"
            "QMenuBar::item:selected,QMenu::item:selected{background:#42414d}"
            "QMenu{background:#1c1b22;color:#e0e0e0;border:1px solid #42414d}"
            "QMenu::item{padding:6px 22px}"
            "QPushButton{background:#2c2c2c;color:#e0e0e0;border:0;padding:6px}"
            "QPushButton:hover{background:#42414d}"
            "QSlider::groove:horizontal{height:4px;background:#4a4a4a}"
            "QSlider::sub-page:horizontal{background:white}"
            "QSlider::handle:horizontal{width:0}"
        )
        self._costruisci_menu()
        centrale = QWidget(self)
        self.setCentralWidget(centrale)
        root = QVBoxLayout(centrale)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.contenuto = QWidget(centrale)
        riga = QHBoxLayout(self.contenuto)
        riga.setContentsMargins(0, 0, 0, 0)
        riga.setSpacing(0)

        self.sinistra = QFrame(self.contenuto)
        self.sinistra.setFixedWidth(300)
        sx = QVBoxLayout(self.sinistra)
        sx.setContentsMargins(8, 8, 8, 8)
        sx.setSpacing(6)
        self.root = self
        self.sessione = Sessione()
        self.tag_cache = leggi_tag()
        self.sottotitoli = {}
        self.colori = leggi_colori()
        self._logo_threads = []
        self._cover_threads = []
        for cartella in self.sessione.config.get("cartelle", []):
            if os.path.isdir(cartella):
                locali = self._media_locale(cartella)
                if locali:
                    self.sessione.canali.extend(locali)
                    self.sessione.liste.append({
                        "percorso": cartella, "nome": os.path.basename(cartella),
                        "canali": [(n, p, ide) for n, p, ide, _cat, _path in locali],
                        "categorie": {p: cat for _n, p, _ide, cat, _path in locali},
                    })
        self.canali = [(n, u, ide) for n, u, ide, _cat, _lista in self.sessione.canali]
        self.epg = self.sessione.epg
        self.epg_nomi = self.sessione.epg_nomi
        self._percorso_attivo = None
        self._categoria_attiva = None
        self.cerca = Ricerca(self.sinistra, self._filtra, vuota=_("Search"))
        sx.addWidget(self.cerca)
        self.elenco = Elenco(self.sinistra)
        self.elenco.singolo = self._seleziona_canale
        self.elenco.itemDoubleClicked.connect(self._apri_selezionato)
        self.elenco.prog_di = self._progresso_di
        sx.addWidget(self.elenco, 1)
        self._riempi_elenco()

        self.video = QWidget(self.contenuto)
        self.video_layout = QHBoxLayout(self.video)
        self.video_layout.setContentsMargins(0, 0, 0, 0)
        self.video_layout.setSpacing(0)
        try:
            self.player = MpvVideo(self.video, options=self._mpv_buffer_options())
            self.video_layout.addWidget(self.player, 1)
            self.player.installEventFilter(self)
        except Exception as errore:
            self.player = None
            avviso = QLabel("libmpv: " + str(errore), self.video)
            avviso.setAlignment(Qt.AlignCenter)
            avviso.setStyleSheet("color:#9e9e9e")
            self.video_layout.addWidget(avviso, 1)

        self.destra = QFrame(self.contenuto)
        self.destra.setFixedWidth(220)
        dx = QVBoxLayout(self.destra)
        dx.setContentsMargins(8, 8, 8, 8)
        self.et_liste = QLabel(_("Playlists"), self.destra)
        self.et_liste.setStyleSheet("color:#9e9e9e")
        dx.addWidget(self.et_liste)
        self.el_liste = Sidebar(self.destra)
        self.el_liste.selected.connect(self._scegli_voce_liste)
        dx.addWidget(self.el_liste, 1)
        self._riempi_liste()

        riga.addWidget(self.sinistra)
        riga.addWidget(self.video, 1)
        riga.addWidget(self.destra)
        root.addWidget(self.contenuto, 1)

        self.barra = QFrame(centrale)
        self.barra.setFixedHeight(96)
        comandi = QVBoxLayout(self.barra)
        comandi.setContentsMargins(12, 5, 12, 5)
        comandi.setSpacing(5)
        controlli = QHBoxLayout()
        self.stop_button = QPushButton("■", self.barra)
        self.precedente_button = QPushButton("◀", self.barra)
        self.play_button = QPushButton("▶", self.barra)
        self.successivo_button = QPushButton("▶|", self.barra)
        for b in (self.stop_button, self.precedente_button, self.play_button, self.successivo_button):
            b.setFixedSize(38, 38)
            controlli.addWidget(b)
        controlli.addStretch(1)
        self.volume = QSlider(Qt.Horizontal, self.barra)
        self.volume.setRange(0, 100)
        self.volume.setValue(int(self.sessione.config.get("volume", 100)))
        self.volume.setFixedWidth(120)
        controlli.addWidget(QLabel("Volume", self.barra))
        controlli.addWidget(self.volume)
        comandi.addLayout(controlli)
        self.posizione = QSlider(Qt.Horizontal, self.barra)
        self.posizione.setRange(0, 1000)
        comandi.addWidget(self.posizione)
        root.addWidget(self.barra)

        self.riga_stato = QLabel("XVB", centrale)
        self.riga_stato.setFixedHeight(28)
        self.riga_stato.setContentsMargins(8, 0, 8, 0)
        self.riga_stato.setStyleSheet("background:#121217;color:#9e9e9e")
        root.addWidget(self.riga_stato)

        self.stop_button.clicked.connect(self.ferma)
        self.precedente_button.clicked.connect(lambda: self.salta(-1))
        self.successivo_button.clicked.connect(lambda: self.salta(+1))
        self.play_button.clicked.connect(self.pausa)
        self.volume.valueChanged.connect(self._volume)
        self.posizione.sliderReleased.connect(self._seek)
        self._pieno = False
        self.player2 = None
        self.player_pip = None
        self.pip_window = None
        self._chiudendo_pip = False
        self.split = False
        self.schermo_attivo = 0
        self.nome_in_onda = ""
        self.ide_in_onda = None
        self.file_in_onda = None
        self.registrando = ""
        self.inizio_rec = 0.0
        self.fine_rec = 0.0
        self.piano = None
        self._timer_rec = QTimer(self)
        self._timer_rec.timeout.connect(self.controlla_registrazione)
        self._timer_rec.start(1000)
        self.mpv = self.player
        self._mpris = avvia_mpris(self)
        self._indice_canale = -1
        self._giro_traccia = 0
        self.ripeti = self.sessione.config.get("ripeti", "")
        self.shuffle_attivo = bool(self.sessione.config.get("shuffle"))
        self._epg_sessione = self.sessione
        self._thread_epg = _CaricaGuide(self._epg_sessione)
        self._thread_epg.completato.connect(self._epg_pronto)
        self._thread_epg.errore.connect(self._epg_errore)
        self._thread_epg.start()
        self._timer_player = QTimer(self)
        self._timer_player.timeout.connect(self._aggiorna_player)
        self._timer_player.start(500)
        self._aggiorna_recenti()
        self.applica_filtri_audio()
        self._volume(self.volume.value())


    def _aggiorna_player(self):
        if not self.player:
            return
        try:
            posizione = self.player.leggi("time-pos")
            durata = self.player.leggi("duration")
            if posizione and durata and not self.posizione.isSliderDown():
                totale = float(durata)
                if totale > 0:
                    self.posizione.setValue(int(float(posizione) * 1000 / totale))
        except Exception:
            return



    def cambia_lingua(self, codice):
        imposta_lingua(codice)
        self.sessione.config["lingua"] = codice
        scrivi_config(self.sessione.config)
        self.menuBar().clear()
        self._costruisci_menu()
        self.et_liste.setText(_("Playlists"))
        self.cerca.casella.setPlaceholderText(_("Search"))
        self._aggiorna_recenti()
        self.riga_stato.setText(_("ready"))

    def buffer_attuale(self):
        chiave = self.sessione.config.get("buffer", "standard")
        return next((voce for voce in BUFFER if voce[0] == chiave), BUFFER[2])

    def _mpv_buffer_options(self):
        voce = self.buffer_attuale()
        return {
            "demuxer-max-bytes": str(voce[2] * 1048576),
            "demuxer-max-back-bytes": str(voce[3] * 1048576),
            "demuxer-readahead-secs": str(voce[4]),
            "cache-pause-wait": str(voce[5]),
        }

    def metti_buffer(self, chiave):
        voce = next((v for v in BUFFER if v[0] == chiave), None)
        if voce is None:
            return
        self.sessione.config["buffer"] = chiave
        scrivi_config(self.sessione.config)
        for player in (self.player, self.player2):
            if player:
                for nome, valore in (("demuxer-max-bytes", voce[2] * 1048576),
                                     ("demuxer-max-back-bytes", voce[3] * 1048576),
                                     ("demuxer-readahead-secs", voce[4]),
                                     ("cache-pause-wait", voce[5])):
                    try:
                        player.imposta(nome, valore)
                    except Exception:
                        pass
        self.riga_stato.setText("Buffer: " + voce[1])

    def _azione(self, nome, callback, scorciatoia=None):
        azione = QAction(nome, self)
        if scorciatoia:
            azione.setShortcut(QKeySequence(scorciatoia))
        azione.triggered.connect(callback)
        return azione

    def _costruisci_menu(self):
        media = self.menuBar().addMenu(_("Media"))
        media.addAction(self._azione(_("Open file..."), self.apri_file, "Ctrl+O"))
        media.addAction(self._azione(_("Open folder..."), self.apri_cartella))
        media.addAction(self._azione(_("Open URL..."), self.apri_url, "Ctrl+L"))
        self.menu_recenti = media.addMenu(_("Recent"))
        media.addAction(self._azione(_("Clear recent"), self.pulisci_recenti))
        media.addSeparator()
        media.addAction(self._azione(_("Quit"), self.close, "Ctrl+Q"))
        playback = self.menuBar().addMenu(_("Playback"))
        playback.addAction(self._azione(_("Play / Pause"), self.pausa, "Space"))
        playback.addAction(self._azione(_("Stop"), self.ferma, "S"))
        playback.addAction(self._azione(_("Back 10 s"), lambda: self._comando("seek", "-10", "relative")))
        playback.addAction(self._azione(_("Forward 10 s"), lambda: self._comando("seek", "10", "relative")))
        playback.addSeparator()
        for velocita in (0.5, 0.75, 1, 1.25, 1.5, 2):
            playback.addAction(self._azione("Speed x%g" % velocita,
                                            lambda _=False, v=velocita: self._imposta("speed", v)))
        playback.addAction(self._azione("Repeat file", lambda: self._ciclo_valori("loop-file", "no", "inf")))
        playback.addAction(self._azione("Repeat playlist", lambda: self._ciclo_valori("loop-playlist", "no", "inf")))
        video = self.menuBar().addMenu(_("Video"))
        for nome, valore in (("Auto", "-1"), ("16:9", "16:9"), ("4:3", "4:3"), ("21:9", "21:9")):
            video.addAction(self._azione("Aspect " + nome,
                                         lambda _=False, v=valore: self._imposta("video-aspect-override", v)))
        video.addAction(self._azione(_("Deinterlace"), lambda: self._ciclo("deinterlace")))
        video.addAction(self._azione(_("Hardware decoding"), lambda: self._ciclo_valori("hwdec", "no", "auto-safe")))
        video.addSeparator()
        for nome, valore in (("Brightness +", ("brightness", 10)), ("Brightness -", ("brightness", -10)),
                             ("Contrast +", ("contrast", 10)), ("Contrast -", ("contrast", -10)),
                             ("Saturation +", ("saturation", 10)), ("Saturation -", ("saturation", -10))):
            video.addAction(self._azione(nome, lambda _=False, v=valore: self._regola(*v)))
        video.addAction(self._azione(_("Reset picture"), lambda: self._azzera_video()))
        video.addAction(self._azione(_("Screenshot"), lambda: self._comando("screenshot")))
        audio = self.menuBar().addMenu(_("Audio"))
        audio.addAction(self._azione(_("Next audio track"), lambda: self._ciclo("aid")))
        audio.addAction(self._azione(_("Next subtitle track"), lambda: self._ciclo("sid")))
        self.menu_tracce_audio = audio.addMenu(_("Audio tracks"))
        self.menu_tracce_sub = audio.addMenu(_("Subtitles"))
        self.menu_tracce_audio.aboutToShow.connect(lambda: self._riempi_menu_tracce(self.menu_tracce_audio, "audio"))
        self.menu_tracce_sub.aboutToShow.connect(lambda: self._riempi_menu_tracce(self.menu_tracce_sub, "sub"))
        audio.addAction(self._azione(_("Load subtitles..."), self.carica_sottotitoli))
        audio.addAction(self._azione(_("Subtitles on/off"), lambda: self._ciclo("sub-visibility")))
        audio.addAction(self._azione("Subtitle delay +100 ms", lambda: self._regola("sub-delay", 0.1)))
        audio.addAction(self._azione("Subtitle delay -100 ms", lambda: self._regola("sub-delay", -0.1)))
        audio.addAction(self._azione("Audio delay +100 ms", lambda: self._regola("audio-delay", 0.1)))
        audio.addAction(self._azione("Audio delay -100 ms", lambda: self._regola("audio-delay", -0.1)))
        audio.addSeparator()
        audio.addAction(self._azione(_("Volume boost +50%"), self.boost))
        audio.addAction(self._azione(_("Normalize loudness"), self.normalizza))
        audio.addAction(self._azione(_("Audio equalizer..."), self.equalizzatore_audio))
        iptv = self.menuBar().addMenu(_("IPTV"))
        iptv.addAction(self._azione(_("Add playlist URL"), self.aggiungi_lista_url))
        iptv.addAction(self._azione(_("Open playlists folder"), self.apri_cartella_liste))
        iptv.addAction(self._azione(_("Reload playlists"), self.ricarica_liste))
        iptv.addSeparator()
        iptv.addAction(self._azione(_("Programme guide"), self.apri_guida))
        iptv.addAction(self._azione(_("Add guide URL"), self.aggiungi_epg_url))
        iptv.addAction(self._azione(_("Reload guide"), self.ricarica_guida))
        iptv.addSeparator()
        iptv.addAction(self._azione(_("Record now / Stop recording"), self.registra))
        iptv.addAction(self._azione(_("Schedule..."), self.pianifica))
        iptv.addAction(self._azione(_("Cancel schedule"), self.annulla_piano))
        iptv.addAction(self._azione(_("Open recordings folder"), self.apri_registrazioni))
        view = self.menuBar().addMenu(_("View"))
        view.addAction(self._azione(_("Fullscreen"), self.schermo_intero, "F"))
        view.addAction(self._azione(_("Picture in picture"), self.pip_si_no))
        view.addAction(self._azione(_("Split screen"), self.split_si_no, "F2"))
        lingua = view.addMenu(_("Language"))
        for codice, nome in LINGUE:
            lingua.addAction(self._azione(nome, lambda _=False, c=codice: self.cambia_lingua(c)))
        buffer_menu = view.addMenu(_("Buffer"))
        for chiave, etichetta, *_resto in BUFFER:
            buffer_menu.addAction(self._azione(etichetta, lambda _=False, k=chiave: self.metti_buffer(k)))
        help_menu = self.menuBar().addMenu(_("Help"))
        help_menu.addAction(self._azione(_("About XVB"), self.informazioni))




    def _attivo(self):
        return self.player2 if self.split and self.schermo_attivo == 1 and self.player2 else self.player

    def _comando(self, *argomenti):
        player = self._attivo()
        if player:
            player.comando(*argomenti)

    def _imposta(self, nome, valore):
        player = self._attivo()
        if player:
            player.imposta(nome, valore)

    def _ciclo(self, nome):
        player = self._attivo()
        if player:
            player.ciclo(nome)

    def _ciclo_valori(self, nome, *valori):
        player = self._attivo()
        if player:
            player.comando("cycle-values", nome, *valori)

    def _regola(self, nome, valore):
        player = self._attivo()
        if player:
            player.regola(nome, valore)

    def _azzera_video(self):
        player = self._attivo()
        if player:
            for nome in ("brightness", "contrast", "saturation", "gamma", "hue"):
                player.imposta(nome, 0)


    def aggiungi_lista_url(self):
        url, ok = QInputDialog.getText(self, _("Add playlist URL"), "URL")
        if not ok or not url.strip():
            return
        cfg = self.sessione.config
        liste = cfg.get("liste", [])
        if isinstance(liste, str):
            liste = [liste]
        if url.strip() not in liste:
            liste.append(url.strip())
        cfg["liste"] = liste
        scrivi_config(cfg)
        self.ricarica_liste()

    def ricarica_liste(self):
        precedente = self.sessione
        nuova = Sessione()
        nuova.epg = precedente.epg
        nuova.epg_nomi = precedente.epg_nomi
        for lista in precedente.liste:
            if lista["percorso"].startswith(("http://", "https://")):
                continue
            if os.path.isdir(lista["percorso"]):
                nuovi = [voce for voce in precedente.canali
                         if voce[4] == lista["percorso"]]
                if nuovi:
                    nuova.canali.extend(nuovi)
                    nuova.liste.append(lista)
        self.sessione = nuova
        self.canali = [(n, u, ide) for n, u, ide, _cat, _lista in nuova.canali]
        self.epg = nuova.epg
        self.epg_nomi = nuova.epg_nomi
        self._percorso_attivo = None
        self._categoria_attiva = None
        self._riempi_liste()
        self._riempi_elenco()
        self.riga_stato.setText("%d channels" % len(self.sessione.canali))

    def apri_cartella_liste(self):
        percorso = CARTELLE_LISTE[0]
        os.makedirs(percorso, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(percorso))

    def aggiungi_epg_url(self):
        url, ok = QInputDialog.getText(self, _("Add guide URL"), "URL")
        if not ok or not url.strip():
            return
        cfg = self.sessione.config
        guide = cfg.get("epg", [])
        if isinstance(guide, str):
            guide = [guide] if guide else []
        if url.strip() not in guide:
            guide.append(url.strip())
        cfg["epg"] = guide
        scrivi_config(cfg)
        self.ricarica_guida()

    def _epg_pronto(self):
        self.sessione.epg = self._epg_sessione.epg
        self.sessione.epg_nomi = self._epg_sessione.epg_nomi
        self.epg = self.sessione.epg
        self.epg_nomi = self.sessione.epg_nomi
        self.riga_stato.setText("EPG ready")

    def _epg_errore(self, errore):
        self.riga_stato.setText("EPG: " + errore)

    def ricarica_guida(self):
        if self._thread_epg.isRunning():
            return
        self.sessione.epg = {}
        self.sessione.epg_nomi = {}
        self._epg_sessione = self.sessione
        self._thread_epg = _CaricaGuide(self._epg_sessione)
        self._thread_epg.completato.connect(self._epg_pronto)
        self._thread_epg.errore.connect(self._epg_errore)
        self._thread_epg.start()

    def apri_guida(self):
        if not self.epg:
            self.riga_stato.setText("EPG data not available")
            return
        self.canali = [(n, u, ide) for n, u, ide, _cat, _lista in self.sessione.canali]
        self.epg = self.sessione.epg
        self.epg_nomi = self.sessione.epg_nomi
        self._finestra_guida = Guida(self)
        self._finestra_guida.show()

    def colore_canale(self, nome, url):
        return "#a78bfa"

    def apri_canale_guida(self, nome, url, ide=None):
        self.apri(url)


    def _riempi_liste(self):
        self.el_liste.clear()
        percorso_iptv = self.el_liste.insert(
            "", "end", iid="iptv", text=" IPTV",
            image=QPixmap("icone/tv.png"), open=True)
        percorso_epg = self.el_liste.insert(
            percorso_iptv, "end", iid="epg", text=" EPG (%d)" % len(self.sessione.config.get("epg", [])),
            open=bool(self.sessione.config.get("epg")))
        for indice, guida in enumerate(self.sessione.config.get("epg", [])):
            self.el_liste.insert(percorso_epg, "end", iid="epg:%d" % indice,
                                 text=" " + os.path.basename(str(guida)))
        percorso_m3u = self.el_liste.insert(
            percorso_iptv, "end", iid="m3u", text=" M3U (%d)" % len(self.sessione.liste),
            open=True)
        percorso_locale = self.el_liste.insert(
            "", "end", iid="locale", text=" Local", open=True)
        for indice, lista in enumerate(self.sessione.liste):
            locale = os.path.isdir(lista["percorso"])
            parent = percorso_locale if locale else percorso_m3u
            iid = "lista:%d" % indice
            nodo = self.el_liste.insert(
                parent, "end", iid=iid,
                text=" " + lista["nome"],
                image=QPixmap("icone/player.png") if locale else None,
                open=locale)
            self.el_liste.item(iid, valore=(lista["percorso"], None))
            categorie = sorted(set(lista["categorie"].values()), key=str.casefold)
            for j, categoria in enumerate(categorie):
                figlio = self.el_liste.insert(
                    nodo, "end", iid="%s:cat:%d" % (iid, j),
                    text=" " + categoria)
                self.el_liste.item(figlio, valore=(lista["percorso"], categoria))
        if self.sessione.preferiti:
            preferiti = self.el_liste.insert(
                percorso_iptv, "end", iid="preferiti",
                text=" " + _("Favorites"), open=True)
            categorie = sorted(
                {voce[3] or "MyPlaylist" for voce in self.sessione.preferiti},
                key=str.casefold)
            for j, categoria in enumerate(categorie):
                figlio = self.el_liste.insert(
                    preferiti, "end", iid="preferiti:%d" % j,
                    text=" " + categoria)
                self.el_liste.item(figlio, valore=("__favorite__", categoria))
        self.el_liste.item(percorso_iptv, valore=(None, None))
        self.el_liste.item(percorso_epg, valore=("__epg__", None))
        self.el_liste.item(percorso_m3u, valore=(None, None))
        self.el_liste.item(percorso_locale, valore=(None, None))

