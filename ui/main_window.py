from PySide6.QtCore import Qt, QUrl, QThread, Signal, QTimer, QSize
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
        comandi.addWidget(self.posizione if hasattr(self, "posizione") else QWidget(self.barra)) if False else None
        self.posizione = QSlider(Qt.Horizontal, self.barra)
        self.posizione.setRange(0, 1000)
        self.posizione.setFixedHeight(10)
        self.posizione.setStyleSheet(
            "QSlider::groove:horizontal{height:2px;background:#4a4a4a}"
            "QSlider::sub-page:horizontal{background:#ffffff}"
            "QSlider::handle:horizontal{width:0;height:0;border:0}")
        self.posizione.sliderReleased.connect(self._seek)
        comandi.addWidget(self.posizione)

        controlli = QHBoxLayout()
        controlli.setSpacing(4)
        self._pulsanti = {}

        def pulsante(chiave, nome, callback, lato=24, etichetta=None):
            b = QPushButton(self.barra)
            percorso = os.path.join("icone", nome + ".png")
            if os.path.isfile(percorso):
                b.setIcon(QIcon(percorso))
                b.setIconSize(QSize(lato, lato))
                b.setFixedSize(lato + 10, lato + 10)
            else:
                b.setText(etichetta or nome)
                b.setFixedSize(max(34, lato + 10), lato + 10)
            b.setToolTip(etichetta or nome)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(callback)
            self._pulsanti[chiave] = b
            controlli.addWidget(b)
            return b

        pulsante("precedente", "prima", lambda: self.salta(-1), 34, _("Previous"))
        pulsante("indietro", "-10", lambda: self.avanza(-10), 24, "-10")
        self.play_button = pulsante("play", "play", self.pausa, 48, _("Play"))
        pulsante("stop", "stop", self.ferma, 34, _("Stop"))
        pulsante("avanti", "+10", lambda: self.avanza(10), 24, "+10")
        pulsante("successivo", "dopo", lambda: self.salta(1), 34, _("Next"))
        pulsante("rec", "rec", self.registra, 24, _("Record"))
        pulsante("repeat", "repeat", self._ciclo_ripeti, 24, _("Repeat"))
        pulsante("shuffle", "shuffle", lambda: self.mpris_shuffle(not self.shuffle_attivo), 24, _("Shuffle"))
        controlli.addStretch(1)
        pulsante("pip", "pip", self.pip_si_no, 24, "PiP")
        pulsante("split", "setting", self.split_si_no, 24, _("Split screen"))
        pulsante("sidebar", "playlist", self._sidebar, 24, _("Playlists"))
        pulsante("fullscreen", "pieno", self.schermo_intero, 24, _("Fullscreen"))
        pulsante("mute", "volume", self._muto, 24, _("Mute"))
        self.volume = QSlider(Qt.Horizontal, self.barra)
        self.volume.setRange(0, 100)
        self.volume.setValue(int(self.sessione.config.get("volume", 85)))
        self.volume.setFixedWidth(85)
        controlli.addWidget(self.volume)
        comandi.addLayout(controlli)


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
        if url.startswith(REGISTRAZIONI + os.sep):
            return colore_di(os.path.basename(os.path.dirname(url)))
        if os.path.isabs(url):
            try:
                posizione = next(i for i, voce in enumerate(self.sessione.canali) if voce[1] == url)
            except StopIteration:
                posizione = 0
            return SCALA_FILE[posizione % len(SCALA_FILE)]
        return (self.sessione.config.get("colori_canali", {}).get(url)
                or self.colori.get(url) or colore_di(nome))

    def apri_canale_guida(self, nome, url, ide=None):
        self.apri(url)


    def _riempi_liste(self):
        self.el_liste.clear()
        iptv = self.el_liste.insert("", "end", iid="iptv", text=" IPTV",
                                    image=QPixmap("icone/tv.png"), open=True)
        epg = self.el_liste.insert(iptv, "end", iid="epg",
                                   text=" EPG (%d)" % len(self.sessione.config.get("epg", [])),
                                   open=bool(self.sessione.config.get("epg")))
        for indice, guida in enumerate(self.sessione.config.get("epg", [])):
            self.el_liste.insert(epg, "end", iid="epg:%d" % indice,
                                 text=" " + os.path.basename(str(guida)))
        m3u = self.el_liste.insert(iptv, "end", iid="m3u",
                                   text=" M3U (%d)" % len(self.sessione.liste),
                                   open=True)
        locale = self.el_liste.insert("", "end", iid="locale",
                                      text=" Local", open=True)
        for indice, lista in enumerate(self.sessione.liste):
            locale_lista = os.path.isdir(lista["percorso"])
            padre = locale if locale_lista else m3u
            iid = "lista:%d" % indice
            nodo = self.el_liste.insert(
                padre, "end", iid=iid, text=" " + lista["nome"],
                image=QPixmap("icone/player.png") if locale_lista else None,
                open=locale_lista)
            self.el_liste.item(iid, valore=(lista["percorso"], None))
            categorie = sorted(set(lista["categorie"].values()), key=str.casefold)
            for j, categoria in enumerate(categorie):
                figlio = self.el_liste.insert(
                    nodo, "end", iid="%s:cat:%d" % (iid, j),
                    text=" " + categoria)
                self.el_liste.item(figlio, valore=(lista["percorso"], categoria))
        if self.sessione.preferiti:
            preferiti = self.el_liste.insert(
                iptv, "end", iid="preferiti", text=" " + _("Favorites"), open=True)
            categorie = sorted(
                {voce[3] or "MyPlaylist" for voce in self.sessione.preferiti},
                key=str.casefold)
            for j, categoria in enumerate(categorie):
                figlio = self.el_liste.insert(
                    preferiti, "end", iid="preferiti:%d" % j,
                    text=" " + categoria)
                self.el_liste.item(figlio, valore=("__favorite__", categoria))
        self.el_liste.item(iptv, valore=(None, None))
        self.el_liste.item(epg, valore=("__epg__", None))
        self.el_liste.item(m3u, valore=(None, None))
        self.el_liste.item(locale, valore=(None, None))

    def _scegli_voce_liste(self, item, _colonna=0):
        dati = self.el_liste.item(item, "valore") if isinstance(item, str) else item.data(0, Qt.UserRole)
        if not dati:
            return
        self._percorso_attivo, self._categoria_attiva = dati
        self._riempi_elenco()

    def _filtra(self, *_):
        self._riempi_elenco()

    def _riempi_elenco(self):
        if not hasattr(self, "elenco"):
            return
        percorso = self._percorso_attivo
        categoria = self._categoria_attiva
        ricerca = self.cerca.get() if hasattr(self, "cerca") else ""
        self.elenco.delete(*self.elenco.get_children())
        self._canali_visibili = [voce for voce in self.sessione.canali
                                 if (percorso is None or voce[4] == percorso)
                                 and (categoria is None or voce[3] == categoria)
                                 and (not ricerca or ricerca.casefold() in (voce[0] + " " + self.sottotitoli.get(voce[1], "") + " " + voce[1]).casefold())]
        for i, voce in enumerate(self._canali_visibili):
            nome, url, ide, gruppo, _lista = voce
            sotto = self.sottotitoli.get(url) or gruppo
            self.elenco.insert("", "end", iid=str(i), text=nome + "\n" + sotto,
                               colore=self.colore_canale(nome, url), logo=self.logo_di(url))

    def _seleziona_canale(self):
        selezione = self.elenco.selection()
        if not selezione:
            return
        voce = self._canali_visibili[int(selezione[0])]
        self._indice_canale = int(selezione[0])
        self.riga_stato.setText(voce[0])
        self.apri(voce[1], nome=voce[0], ide=voce[2])

    def _apri_selezionato(self, _item=None):
        selezione = self.elenco.selection()
        if selezione:
            voce = self._canali_visibili[int(selezione[0])]
            self._indice_canale = int(selezione[0])
            self.apri(voce[1], nome=voce[0], ide=voce[2])




    def colore_canale(self, nome, url):
        if os.path.isabs(url):
            try:
                posizione = next(i for i, voce in enumerate(self.sessione.canali) if voce[1] == url)
            except StopIteration:
                posizione = 0
            return SCALA_FILE[posizione % len(SCALA_FILE)]
        return (self.sessione.config.get("colori_canali", {}).get(url)
                or self.colori.get(url) or colore_di(nome))

    def logo_di(self, url):
        if os.path.isabs(url):
            estensione = os.path.splitext(url)[1][1:].lower()
            if estensione in AUDIO:
                percorso = copertina_url(url)
                if os.path.isfile(percorso):
                    pix = QPixmap(percorso)
                    return pix if not pix.isNull() else None
                if not any(w.url == url and w.isRunning() for w in self._cover_threads):
                    worker = _CaricaCopertina(url, percorso)
                    worker.completato.connect(self._copertina_pronta)
                    worker.finished.connect(lambda w=worker: self._rimuovi_worker_copertina(w))
                    self._cover_threads.append(worker)
                    worker.start()
                return None
            poster = poster_film(url)
            return QPixmap(poster) if poster else None
        logo = LOGHI.get(url)
        if not logo:
            return None
        import hashlib
        percorso = os.path.join(CACHE_LOGHI, hashlib.md5(logo.encode()).hexdigest())
        if os.path.isfile(percorso) and os.path.getsize(percorso):
            pix = QPixmap(percorso)
            return pix if not pix.isNull() else None
        if not any(w.url == url and w.isRunning() for w in self._logo_threads):
            worker = _ScaricaColoreLogo(url, logo)
            worker.completato.connect(self._logo_pronto)
            worker.finished.connect(lambda w=worker: self._rimuovi_worker_logo(w))
            self._logo_threads.append(worker)
            worker.start()
        return None


    def _rimuovi_worker_copertina(self, worker):
        if worker in self._cover_threads:
            self._cover_threads.remove(worker)

    def _copertina_pronta(self, _url):
        if hasattr(self, "elenco"):
            self._riempi_elenco()

    def _rimuovi_worker_logo(self, worker):
        if worker in self._logo_threads:
            self._logo_threads.remove(worker)

    def _logo_pronto(self, url, colore):
        if colore:
            self.colori[url] = colore
            scrivi_colori(self.colori)
        if hasattr(self, "elenco"):
            self._riempi_elenco()
        if getattr(self, "_finestra_guida", None):
            self._finestra_guida.ridisegna()

    def _progresso_di(self, iid):
        try:
            voce = self._canali_visibili[int(iid)]
            nome, url, ide = voce[:3]
            chiave = ide if ide and ide in self.sessione.epg else self.sessione.epg_nomi.get(
                __import__("core.epg", fromlist=["nome_piatto"]).nome_piatto(nome))
            if not chiave:
                return None
            adesso = time.time()
            for inizio, fine, _titolo in self.sessione.epg.get(chiave, []):
                if inizio <= adesso < fine:
                    return (adesso - inizio) / float(max(1, fine - inizio))
        except Exception:
            return None
        return None

    def _media_locale(self, cartella):
        gia = {voce[1] for voce in self.sessione.canali}
        nuovi = []
        for nome, percorso, ide in media_in(cartella):
            if percorso in gia:
                continue
            estensione = os.path.splitext(percorso)[1][1:].lower()
            if estensione in AUDIO:
                titolo, artista, album, anno = tag_di(percorso, self.tag_cache)
                if not titolo:
                    titolo, artista_file, album_file, anno_file = dal_percorso(percorso, (cartella,))
                    artista = artista or artista_file
                    album = album or album_file
                    anno = anno or anno_file
                nome = titolo or nome
                sotto = " · ".join(x for x in (artista, album, anno) if x)
                categoria = "Music"
            else:
                titolo, anno = titolo_anno(percorso)
                nome = titolo or nome
                sotto = anno or ""
                categoria = "Video"
            self.sottotitoli[percorso] = sotto
            nuovi.append((nome, percorso, ide, categoria, cartella))
        return nuovi

    def apri_cartella(self):
        cartella = QFileDialog.getExistingDirectory(self, _("Open folder"))
        if not cartella:
            return
        nuovi = self._media_locale(cartella)
        if not nuovi:
            self.riga_stato.setText("No media files found")
            return
        self.sessione.canali.extend(nuovi)
        cartelle = self.sessione.config.setdefault("cartelle", [])
        if cartella not in cartelle:
            cartelle.append(cartella)
            scrivi_config(self.sessione.config)
        self.canali.extend((n, p, i) for n, p, i, _c, _l in nuovi)
        self.sessione.liste.append({
            "percorso": cartella, "nome": os.path.basename(cartella),
            "canali": [(n, p, i) for n, p, i, _c, _l in nuovi],
            "categorie": {p: categoria for _n, p, _i, categoria, _l in nuovi},
        })
        self._riempi_liste()
        self._percorso_attivo, self._categoria_attiva = cartella, None
        self._riempi_elenco()
        self.riga_stato.setText("%d media files" % len(nuovi))

    def informazioni(self):
        QMessageBox.about(self, "XVB", _("XVB Player 4.4.4"))




    def tracce(self, tipo):
        player = self._attivo()
        if not player:
            return []
        try:
            valore = player.leggi("track-list")
            elenco = json.loads(valore) if valore else []
            return [traccia for traccia in elenco if traccia.get("type") == tipo]
        except Exception:
            return []

    @staticmethod
    def nome_traccia(traccia):
        nome = traccia.get("title") or traccia.get("lang") or ""
        codec = traccia.get("codec") or ""
        return ("%s (%s)" % (nome, codec) if nome and codec
                else nome or codec or str(traccia.get("id")))

    def _riempi_menu_tracce(self, menu, tipo):
        menu.clear()
        tracce = self.tracce(tipo)
        if not tracce:
            azione = menu.addAction(_("No tracks available"))
            azione.setEnabled(False)
            return
        proprieta = "aid" if tipo == "audio" else "sid"
        for traccia in tracce:
            testo = self.nome_traccia(traccia)
            if traccia.get("selected"):
                testo = "✓  " + testo
            menu.addAction(self._azione(
                testo, lambda _=False, i=traccia.get("id"): self.metti_traccia(proprieta, i)))

    def metti_traccia(self, proprieta, identificativo):
        player = self._attivo()
        if player:
            player.imposta(proprieta, identificativo)

    def carica_sottotitoli(self):
        percorso, _ = QFileDialog.getOpenFileName(
            self, _("Load subtitles"), "", "Subtitles (*.srt *.ass *.ssa *.sub *.vtt *.idx *.sup)")
        if percorso:
            self._comando("sub-add", percorso, "select")

    def boost(self):
        attivo = not bool(self.sessione.config.get("boost"))
        self.sessione.config["boost"] = attivo
        scrivi_config(self.sessione.config)
        self._volume(self.volume.value())

    def normalizza(self):
        attivo = not bool(self.sessione.config.get("normalizza"))
        self.sessione.config["normalizza"] = attivo
        scrivi_config(self.sessione.config)
        self.applica_filtri_audio()

    def applica_filtri_audio(self):
        filtri = []
        if self.sessione.config.get("normalizza"):
            filtri.append("dynaudnorm=f=150:g=15")
        bande = self.sessione.config.get("eq_bande", [0] * 10)
        if not isinstance(bande, list) or len(bande) != 10:
            bande = [0] * 10
        for frequenza, guadagno in zip((31, 62, 125, 250, 500, 1000, 2000, 4000, 8000, 16000), bande):
            guadagno = max(-12, min(12, int(guadagno)))
            if guadagno:
                filtri.append("equalizer=f=%d:width_type=o:width=1:g=%d" % (frequenza, guadagno))
        player = self._attivo()
        if player:
            player.imposta("af", "lavfi=[" + ",".join(filtri) + "]" if filtri else "")

    def equalizzatore_audio(self):
        originali = list(self.sessione.config.get("eq_bande", [0] * 10))
        if len(originali) != 10:
            originali = [0] * 10
        finestra = QDialog(self)
        finestra.setWindowTitle(_("Audio equalizer"))
        finestra.setModal(True)
        finestra.setStyleSheet("QDialog{background:#1c1b22;color:#e0e0e0}")
        layout = QVBoxLayout(finestra)
        col = QHBoxLayout()
        layout.addLayout(col)
        slider = []
        for frequenza, valore in zip(("31", "62", "125", "250", "500", "1k", "2k", "4k", "8k", "16k"), originali):
            cella = QVBoxLayout()
            cella.addWidget(QLabel(frequenza))
            s = QSlider(Qt.Vertical)
            s.setRange(-12, 12)
            s.setValue(int(valore))
            s.valueChanged.connect(lambda _v: self._eq_anteprima(slider))
            slider.append(s)
            cella.addWidget(s)
            col.addLayout(cella)
        comandi = QHBoxLayout()
        flat = QPushButton(_("Flat"))
        cancel = QPushButton(_("Cancel"))
        ok = QPushButton(_("OK"))
        comandi.addWidget(flat)
        comandi.addStretch(1)
        comandi.addWidget(cancel)
        comandi.addWidget(ok)
        layout.addLayout(comandi)
        flat.clicked.connect(lambda: [s.setValue(0) for s in slider])
        cancel.clicked.connect(finestra.reject)
        ok.clicked.connect(finestra.accept)
        finestra.resize(620, 290)
        risultato = finestra.exec()
        if risultato:
            self.sessione.config["eq_bande"] = [s.value() for s in slider]
            scrivi_config(self.sessione.config)
        else:
            self.sessione.config["eq_bande"] = originali
        self.applica_filtri_audio()

    def _eq_anteprima(self, slider):
        self.sessione.config["eq_bande"] = [s.value() for s in slider]
        self.applica_filtri_audio()

    def _aggiorna_mpris(self):
        self.mpv = self._attivo()
        if not self._mpris:
            return
        player = self.mpv
        titolo, artista, album, arte = self.nome_in_onda, "", "", ""
        durata = player.duration if player else 0
        if self.file_in_onda and os.path.isabs(self.file_in_onda):
            tag_titolo, artista, album, _anno = tag_di(self.file_in_onda, self.tag_cache)
            titolo = tag_titolo or titolo
            copertina = copertina_url(self.file_in_onda)
            if os.path.isfile(copertina):
                arte = copertina
        try:
            pausa = player.leggi("pause") == "yes" if player else True
            self._mpris.aggiorna({
                "titolo": titolo,
                "artista": artista,
                "album": album,
                "arte": arte,
                "stato": "Stopped" if not self.file_in_onda else ("Paused" if pausa else "Playing"),
                "volume": self.volume.value() / 100.0,
                "durata": durata,
                "shuffle": self.shuffle_attivo,
                "giro_ripeti": {"uno": "Track", "tutti": "Playlist"}.get(self.ripeti, "None"),
                "giro": self._giro_traccia,
            })
        except Exception:
            pass

    def chiudi(self):
        self.close()

    def mpris_alza(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def mpris_comando(self, comando):
        player = self._attivo()
        if not player:
            return
        if comando == "playpause":
            self.pausa()
        elif comando == "play":
            player.pausa(False)
        elif comando == "pause":
            player.pausa(True)
        self._aggiorna_mpris()

    def mpris_posizione(self, secondi):
        player = self._attivo()
        if player:
            player.seek(secondi)
        self._aggiorna_mpris()

    def avanza(self, secondi):
        player = self._attivo()
        if player:
            player.seek(secondi, assoluto=False)

    def salta(self, direzione):
        if not self._canali_visibili:
            return
        if self._indice_canale < 0:
            self._indice_canale = 0
        if self.shuffle_attivo and len(self._canali_visibili) > 1:
            candidati = [i for i in range(len(self._canali_visibili)) if i != self._indice_canale]
            self._indice_canale = random.choice(candidati)
        else:
            self._indice_canale = (self._indice_canale + direzione) % len(self._canali_visibili)
        voce = self._canali_visibili[self._indice_canale]
        self.apri(voce[1], nome=voce[0], ide=voce[2])

    def mpris_shuffle(self, attivo):
        self.shuffle_attivo = bool(attivo)
        self.sessione.config["shuffle"] = self.shuffle_attivo
        scrivi_config(self.sessione.config)
        self._aggiorna_mpris()

    def metti_ripeti(self, modalita):
        self.ripeti = modalita or ""
        self.sessione.config["ripeti"] = self.ripeti
        scrivi_config(self.sessione.config)
        player = self._attivo()
        if player:
            player.imposta("loop-file", "inf" if self.ripeti == "uno" else "no")
        self._aggiorna_mpris()

    def _programma_corrente(self):
        if not self.ide_in_onda and not self.nome_in_onda:
            return None
        chiave = self.ide_in_onda if self.ide_in_onda in self.sessione.epg else self.sessione.epg_nomi.get(
            __import__("core.epg", fromlist=["nome_piatto"]).nome_piatto(self.nome_in_onda))
        if not chiave:
            return None
        adesso = time.time()
        for programma in self.sessione.epg.get(chiave, []):
            if programma[0] <= adesso < programma[1]:
                return programma
        return None

    def registra(self):
        if self.registrando:
            self.ferma_registrazione()
            return
        f = self.file_in_onda or ""
        if not f.startswith(("http://", "https://")) or not self.nome_in_onda:
            self.riga_stato.setText("Open an IPTV stream before recording")
            return
        self.avvia_registrazione(self.nome_in_onda, 0.0)

    def avvia_registrazione(self, nome, fine):
        player = self._attivo()
        if not player:
            return
        try:
            os.makedirs(REGISTRAZIONI, exist_ok=True)
            programma = self._programma_corrente()
            titolo = (programma[2] if programma and programma[2] else "") or nome
            pulisci = lambda t: re.sub(r'[\\/:*?"<>|]+', "", t).strip() or "xvb"
            cartella = os.path.join(REGISTRAZIONI, pulisci(nome))
            os.makedirs(cartella, exist_ok=True)
            video = player.leggi("vid")
            estensione = "mkv" if video not in (None, "no", "0") else "mka"
            destinazione = os.path.join(
                cartella, "%s - %s.%s" % (
                    pulisci(titolo), time.strftime("%Y-%m-%d %H-%M"), estensione))
            player.imposta("stream-record", destinazione)
        except Exception as errore:
            self.riga_stato.setText("Cannot record: " + str(errore))
            return
        self.registrando = destinazione
        self.fine_rec = fine
        self.inizio_rec = time.time()
        self._mostra_rec()

    def ferma_registrazione(self):
        player = self._attivo()
        if player:
            try:
                player.imposta("stream-record", "")
            except Exception:
                pass
        destinazione = self.registrando
        self.registrando = ""
        self.fine_rec = 0.0
        if destinazione:
            self.riga_stato.setText("Saved " + os.path.basename(destinazione))
            self._riempi_liste()

    def _mostra_rec(self):
        if not self.registrando:
            return
        durata = int(time.time() - self.inizio_rec)
        ore, resto = divmod(durata, 3600)
        cronometro = ("%d:%02d:%02d" % (ore, resto // 60, resto % 60)
                      if ore else "%02d:%02d" % (resto // 60, resto % 60))
        stato = "REC " + cronometro
        if self.fine_rec:
            stato += "  until " + time.strftime("%H:%M", time.localtime(self.fine_rec))
        self.riga_stato.setText(stato)

    @staticmethod
    def ora_di(testo, dopo=None):
        h, m = (int(x) for x in testo.strip().split(":"))
        if not (0 <= h < 24 and 0 <= m < 60):
            raise ValueError(testo)
        adesso = time.localtime()
        t = time.mktime((adesso.tm_year, adesso.tm_mon, adesso.tm_mday,
                         h, m, 0, 0, 0, -1))
        base = dopo if dopo is not None else time.time()
        while t <= base:
            t += 86400
        return t

    def pianifica(self):
        if not self.file_in_onda or not self.nome_in_onda:
            self.riga_stato.setText("Open the channel to record first")
            return
        inizio, ok = QInputDialog.getText(self, _("Schedule"), _("Start (HH:MM):"),
                                          text=time.strftime("%H:%M"))
        if not ok or not inizio:
            return
        fine, ok = QInputDialog.getText(self, _("Schedule"), _("End (HH:MM):"))
        if not ok or not fine:
            return
        try:
            t0 = self.ora_di(inizio)
            t1 = self.ora_di(fine, dopo=t0)
        except (ValueError, TypeError):
            self.riga_stato.setText("Time must be HH:MM")
            return
        self.piano = (self.nome_in_onda, self.file_in_onda, self.ide_in_onda, t0, t1)
        self.riga_stato.setText("Scheduled %s: %s–%s" % (
            self.nome_in_onda, time.strftime("%H:%M", time.localtime(t0)),
            time.strftime("%H:%M", time.localtime(t1))))

    def annulla_piano(self):
        self.piano = None
        self.riga_stato.setText("Schedule cancelled")

    def controlla_registrazione(self):
        adesso = time.time()
        if self.piano and adesso >= self.piano[3]:
            nome, url, ide, _inizio, fine = self.piano
            self.piano = None
            if adesso < fine:
                if self.file_in_onda != url:
                    self.apri(url, nome=nome, ide=ide)
                    QTimer.singleShot(5000, lambda: self.avvia_registrazione(nome, fine))
                else:
                    self.avvia_registrazione(nome, fine)
        if self.registrando and self.fine_rec and adesso >= self.fine_rec:
            self.ferma_registrazione()
        elif self.registrando:
            self._mostra_rec()

    def apri_registrazioni(self):
        os.makedirs(REGISTRAZIONI, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(REGISTRAZIONI))


    def recenti(self):
        return [p for p in self.sessione.config.get("recenti", []) if os.path.isfile(p)][:8]

    def _aggiorna_recenti(self):
        if not hasattr(self, "menu_recenti"):
            return
        self.menu_recenti.clear()
        for percorso in self.recenti():
            self.menu_recenti.addAction(
                self._azione(os.path.basename(percorso), lambda _=False, p=percorso: self.apri(p)))
        self.menu_recenti.setEnabled(bool(self.recenti()))

    def pulisci_recenti(self):
        self.sessione.config["recenti"] = []
        scrivi_config(self.sessione.config)
        self._aggiorna_recenti()

    def apri_file(self):
        percorso, _ = QFileDialog.getOpenFileName(self, _("Open file"))
        if percorso:
            self.apri(percorso)

    def apri_url(self):
        url, ok = QInputDialog.getText(self, _("Open URL"), "URL")
        if ok and url.strip():
            self.apri(url.strip())

    def apri(self, percorso, url=None, ide=None, nome=None):
        if url is not None:
            nome = percorso
            percorso = url
        if self.player is None:
            QMessageBox.warning(self, "XVB", "libmpv non disponibile")
            return
        try:
            player = self._attivo()
            player.apri(percorso)
            self._giro_traccia += 1
            self.file_in_onda = percorso
            if os.path.isfile(percorso):
                recenti = self.sessione.config.get("recenti", [])
                recenti = [p for p in recenti if p != percorso and os.path.isfile(p)]
                self.sessione.config["recenti"] = ([percorso] + recenti)[:8]
                scrivi_config(self.sessione.config)
                self._aggiorna_recenti()
            self.nome_in_onda = nome or os.path.basename(percorso.rstrip("/")) or percorso
            self.ide_in_onda = ide
            self.riga_stato.setText(self.nome_in_onda)
            self.play_button.setText("Ⅱ")
            self._aggiorna_mpris()
        except Exception as errore:
            QMessageBox.critical(self, "XVB", str(errore))

    def pausa(self):
        player = self._attivo()
        if player:
            player.pausa()
            self.play_button.setText("▶" if player.leggi("pause") == "yes" else "Ⅱ")
            self._aggiorna_mpris()

    def ferma(self):
        player = self._attivo()
        if player:
            player.ferma()
            self.file_in_onda = None
            self.nome_in_onda = ""
            self.play_button.setText("▶")
            self.riga_stato.setText("XVB")
            self._aggiorna_mpris()

    def _volume(self, valore):
        player = self._attivo()
        if player:
            player.volume(float(valore) * (1.5 if self.sessione.config.get("boost") else 1.0))
        self.sessione.config["volume"] = int(valore)
        scrivi_config(self.sessione.config)
        self._aggiorna_mpris()

    def _seek(self):
        player = self._attivo()
        if player:
            durata = player.leggi("duration")
            if durata:
                player.seek(float(durata) * self.posizione.value() / 1000.0)


    def eventFilter(self, oggetto, evento):
        if evento.type() == evento.Type.MouseButtonPress:
            if oggetto is self.player:
                self.schermo_attivo = 0
            elif oggetto is self.player2:
                self.schermo_attivo = 1
        return super().eventFilter(oggetto, evento)

    def split_si_no(self):
        if self.split:
            self.chiudi_split()
        else:
            self.apri_split()

    def apri_split(self):
        if self.player is None or self.pip_window is not None:
            return
        try:
            self.player2 = MpvVideo(self.video, options={"mute": "yes"})
            self.player2.installEventFilter(self)
            self.video_layout.addWidget(self.player2, 1)
            self.split = True
            self.schermo_attivo = 0
        except Exception as errore:
            self.player2 = None
            self.riga_stato.setText("Split screen failed: " + str(errore))

    def chiudi_split(self):
        if not self.split:
            return
        self.schermo_attivo = 0
        self.split = False
        self.player2.ferma()
        self.video_layout.removeWidget(self.player2)
        self.player2.chiudi()
        self.player2.setParent(None)
        self.player2.deleteLater()
        self.player2 = None

    def pip_si_no(self):
        if self.pip_window is not None:
            self.esci_pip()
            return
        if not self.player or not self.file_in_onda:
            return
        try:
            posizione = float(self.player.leggi("time-pos") or 0)
            self.player.pausa(True)
            self.pip_window = QDialog(self, Qt.Tool | Qt.WindowStaysOnTopHint)
            self.pip_window.setWindowTitle("XVB")
            layout = QVBoxLayout(self.pip_window)
            layout.setContentsMargins(0, 0, 0, 0)
            self.player_pip = MpvVideo(self.pip_window)
            layout.addWidget(self.player_pip)
            self.player_pip.apri(self.file_in_onda)
            if posizione:
                self.player_pip.seek(posizione)
            self.pip_window.resize(480, 270)
            self.pip_window.finished.connect(self._pip_finestra_chiusa)
            self.pip_window.show()
        except Exception as errore:
            self.riga_stato.setText("Picture in picture failed: " + str(errore))
            self.esci_pip()

    def _pip_finestra_chiusa(self, *_):
        if not self._chiudendo_pip:
            self.esci_pip(chiudi_finestra=False)

    def esci_pip(self, chiudi_finestra=True):
        if self.pip_window is None:
            return
        finestra, player = self.pip_window, self.player_pip
        self.pip_window = None
        self.player_pip = None
        self._chiudendo_pip = True
        posizione = 0.0
        if player:
            try:
                posizione = float(player.leggi("time-pos") or 0)
                player.chiudi()
            except Exception:
                pass
        if chiudi_finestra:
            finestra.close()
        finestra.deleteLater()
        self._chiudendo_pip = False
        if self.player:
            if posizione:
                self.player.seek(posizione)
            self.player.pausa(False)

    def schermo_intero(self):
        if self.isFullScreen():
            self.showNormal()
            self.menuBar().show()
            self.barra.show()
            self.sinistra.show()
            self.destra.show()
        else:
            self.menuBar().hide()
            self.barra.hide()
            self.sinistra.hide()
            self.destra.hide()
            self.showFullScreen()

    def closeEvent(self, evento):
        self._timer_player.stop()
        self._timer_rec.stop()
        if self._thread_epg.isRunning():
            self._thread_epg.wait(65000)
        for worker in self._logo_threads + self._cover_threads:
            if worker.isRunning():
                worker.wait(12000)
        scrivi_tag(self.tag_cache)
        if self.pip_window is not None:
            self.esci_pip()
        if self.player2:
            self.player2.chiudi()
            self.player2 = None
        if self.player:
            self.player.chiudi()
        super().closeEvent(evento)
