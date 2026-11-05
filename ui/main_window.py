from PySide6.QtCore import Qt, QUrl, QThread, Signal, QTimer
from PySide6.QtGui import QAction, QKeySequence, QIcon, QDesktopServices
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QDialog,
    QPushButton, QFileDialog, QInputDialog, QMessageBox, QSlider, QTreeWidget, QTreeWidgetItem
)
from engine.mpv import MpvVideo
from ui.widgets import Elenco, Ricerca, Guida
from core.session import Sessione
from core.media import media_in, AUDIO
from core.tags import leggi_tag, tag_di, scrivi_tag
from core.metadata import titolo_anno, dal_percorso
from integrations.mpris import avvia_mpris
from core.config import scrivi_config, CARTELLE_LISTE, REGISTRAZIONI
from core.playlists import liste_in_cartella, BUFFER
import os
import re
import time


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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
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
        self.cerca = Ricerca(self.sinistra, self._filtra, vuota="Search")
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
        self.et_liste = QLabel("Playlists", self.destra)
        self.et_liste.setStyleSheet("color:#9e9e9e")
        dx.addWidget(self.et_liste)
        self.el_liste = QTreeWidget(self.destra)
        self.el_liste.setHeaderHidden(True)
        self.el_liste.setRootIsDecorated(True)
        self.el_liste.setIndentation(14)
        self.el_liste.setStyleSheet(
            "QTreeWidget{background:#1c1b22;border:0;color:#e0e0e0}"
            "QTreeWidget::item{height:32px}"
            "QTreeWidget::item:selected{background:#42414d;color:#e9ddff}")
        self.el_liste.itemClicked.connect(self._scegli_voce_liste)
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
        self.volume.setRange(0, 150)
        self.volume.setValue(100)
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
        self.ripeti = ""
        self.shuffle_attivo = False
        self._epg_sessione = self.sessione
        self._thread_epg = _CaricaGuide(self._epg_sessione)
        self._thread_epg.completato.connect(self._epg_pronto)
        self._thread_epg.errore.connect(self._epg_errore)
        self._thread_epg.start()
        self._timer_player = QTimer(self)
        self._timer_player.timeout.connect(self._aggiorna_player)
        self._timer_player.start(500)


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
        media = self.menuBar().addMenu("Media")
        media.addAction(self._azione("Open file...", self.apri_file, "Ctrl+O"))
        media.addAction(self._azione("Open folder...", self.apri_cartella))
        media.addAction(self._azione("Open URL...", self.apri_url, "Ctrl+L"))
        media.addSeparator()
        media.addAction(self._azione("Quit", self.close, "Ctrl+Q"))
        playback = self.menuBar().addMenu("Playback")
        playback.addAction(self._azione("Play / Pause", self.pausa, "Space"))
        playback.addAction(self._azione("Stop", self.ferma, "S"))
        playback.addAction(self._azione("Back 10 s", lambda: self._comando("seek", "-10", "relative")))
        playback.addAction(self._azione("Forward 10 s", lambda: self._comando("seek", "10", "relative")))
        playback.addSeparator()
        for velocita in (0.5, 0.75, 1, 1.25, 1.5, 2):
            playback.addAction(self._azione("Speed x%g" % velocita,
                                            lambda _=False, v=velocita: self._imposta("speed", v)))
        playback.addAction(self._azione("Repeat file", lambda: self._ciclo_valori("loop-file", "no", "inf")))
        playback.addAction(self._azione("Repeat playlist", lambda: self._ciclo_valori("loop-playlist", "no", "inf")))
        video = self.menuBar().addMenu("Video")
        for nome, valore in (("Auto", "-1"), ("16:9", "16:9"), ("4:3", "4:3"), ("21:9", "21:9")):
            video.addAction(self._azione("Aspect " + nome,
                                         lambda _=False, v=valore: self._imposta("video-aspect-override", v)))
        video.addAction(self._azione("Deinterlace", lambda: self._ciclo("deinterlace")))
        video.addAction(self._azione("Hardware decoding", lambda: self._ciclo_valori("hwdec", "no", "auto-safe")))
        video.addSeparator()
        for nome, valore in (("Brightness +", ("brightness", 10)), ("Brightness -", ("brightness", -10)),
                             ("Contrast +", ("contrast", 10)), ("Contrast -", ("contrast", -10)),
                             ("Saturation +", ("saturation", 10)), ("Saturation -", ("saturation", -10))):
            video.addAction(self._azione(nome, lambda _=False, v=valore: self._regola(*v)))
        video.addAction(self._azione("Reset picture", lambda: self._azzera_video()))
        video.addAction(self._azione("Screenshot", lambda: self._comando("screenshot")))
        audio = self.menuBar().addMenu("Audio")
        audio.addAction(self._azione("Next audio track", lambda: self._ciclo("aid")))
        audio.addAction(self._azione("Next subtitle track", lambda: self._ciclo("sid")))
        audio.addAction(self._azione("Subtitles on/off", lambda: self._ciclo("sub-visibility")))
        audio.addAction(self._azione("Subtitle delay +100 ms", lambda: self._regola("sub-delay", 0.1)))
        audio.addAction(self._azione("Subtitle delay -100 ms", lambda: self._regola("sub-delay", -0.1)))
        audio.addAction(self._azione("Audio delay +100 ms", lambda: self._regola("audio-delay", 0.1)))
        audio.addAction(self._azione("Audio delay -100 ms", lambda: self._regola("audio-delay", -0.1)))
        iptv = self.menuBar().addMenu("IPTV")
        iptv.addAction(self._azione("Add playlist URL", self.aggiungi_lista_url))
        iptv.addAction(self._azione("Open playlists folder", self.apri_cartella_liste))
        iptv.addAction(self._azione("Reload playlists", self.ricarica_liste))
        iptv.addSeparator()
        iptv.addAction(self._azione("Programme guide", self.apri_guida))
        iptv.addAction(self._azione("Add guide URL", self.aggiungi_epg_url))
        iptv.addAction(self._azione("Reload guide", self.ricarica_guida))
        iptv.addSeparator()
        iptv.addAction(self._azione("Record now / Stop recording", self.registra))
        iptv.addAction(self._azione("Schedule...", self.pianifica))
        iptv.addAction(self._azione("Cancel schedule", self.annulla_piano))
        iptv.addAction(self._azione("Open recordings folder", self.apri_registrazioni))
        view = self.menuBar().addMenu("View")
        view.addAction(self._azione("Fullscreen", self.schermo_intero, "F"))
        view.addAction(self._azione("Picture in picture", self.pip_si_no))
        view.addAction(self._azione("Split screen", self.split_si_no, "F2"))
        buffer_menu = view.addMenu("Buffer")
        for chiave, etichetta, *_resto in BUFFER:
            buffer_menu.addAction(self._azione(etichetta, lambda _=False, k=chiave: self.metti_buffer(k)))
        help_menu = self.menuBar().addMenu("Help")
        help_menu.addAction(self._azione("About XVB", self.informazioni))




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
        url, ok = QInputDialog.getText(self, "Add playlist URL", "URL")
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
        url, ok = QInputDialog.getText(self, "Add guide URL", "URL")
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
        for lista in self.sessione.liste:
            radice = QTreeWidgetItem([lista["nome"]])
            radice.setData(0, Qt.UserRole, (lista["percorso"], None))
            self.el_liste.addTopLevelItem(radice)
            categorie = sorted(set(lista["categorie"].values()), key=str.casefold)
            for categoria in categorie:
                voce = QTreeWidgetItem([categoria])
                voce.setData(0, Qt.UserRole, (lista["percorso"], categoria))
                radice.addChild(voce)
            radice.setExpanded(True)
        if self.sessione.preferiti:
            preferiti = QTreeWidgetItem(["Favorites"])
            preferiti.setData(0, Qt.UserRole, ("__favorite__", None))
            self.el_liste.addTopLevelItem(preferiti)
            categorie = sorted({voce[3] or "MyPlaylist" for voce in self.sessione.preferiti},
                               key=str.casefold)
            for categoria in categorie:
                voce = QTreeWidgetItem([categoria])
                voce.setData(0, Qt.UserRole, ("__favorite__", categoria))
                preferiti.addChild(voce)
            preferiti.setExpanded(True)

    def _scegli_voce_liste(self, item, _colonna=0):
        dati = item.data(0, Qt.UserRole)
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
                               colore="#9e9e9e")

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
        cartella = QFileDialog.getExistingDirectory(self, "Open folder")
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
        QMessageBox.about(self, "XVB", "XVB Player 4.4.4")



    def _aggiorna_mpris(self):
        self.mpv = self._attivo()
        if not self._mpris:
            return
        player = self.mpv
        try:
            pausa = player.leggi("pause") == "yes" if player else True
            durata = player.duration if player else 0
            self._mpris.aggiorna({
                "titolo": self.nome_in_onda,
                "stato": "Stopped" if not self.file_in_onda else ("Paused" if pausa else "Playing"),
                "volume": self.volume.value() / 100.0,
                "durata": durata,
                "shuffle": self.shuffle_attivo,
                "giro_ripeti": {"uno": "Track", "tutti": "Playlist"}.get(self.ripeti, "None"),
                "giro": int(time.time()),
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
        inizio, ok = QInputDialog.getText(self, "Schedule", "Start (HH:MM):",
                                          text=time.strftime("%H:%M"))
        if not ok or not inizio:
            return
        fine, ok = QInputDialog.getText(self, "Schedule", "End (HH:MM):")
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

    def apri_file(self):
        percorso, _ = QFileDialog.getOpenFileName(self, "Open file")
        if percorso:
            self.apri(percorso)

    def apri_url(self):
        url, ok = QInputDialog.getText(self, "Open URL", "URL")
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
            self.file_in_onda = percorso
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
            player.volume(valore)
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
        scrivi_tag(self.tag_cache)
        if self.pip_window is not None:
            self.esci_pip()
        if self.player2:
            self.player2.chiudi()
            self.player2 = None
        if self.player:
            self.player.chiudi()
        super().closeEvent(evento)
