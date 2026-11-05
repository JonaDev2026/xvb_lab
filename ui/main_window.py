from PySide6.QtCore import Qt, QUrl, QThread, Signal, QTimer
from PySide6.QtGui import QAction, QKeySequence, QIcon, QDesktopServices
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFileDialog, QInputDialog, QMessageBox, QSlider, QTreeWidget, QTreeWidgetItem
)
from engine.mpv import MpvVideo
from ui.widgets import Elenco, Ricerca, Guida
from core.session import Sessione
from core.media import media_in
from core.config import scrivi_config, CARTELLE_LISTE
from core.playlists import liste_in_cartella
import os


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
        sx.addWidget(self.elenco, 1)
        self._riempi_elenco()

        self.video = QWidget(self.contenuto)
        self.video_layout = QVBoxLayout(self.video)
        self.video_layout.setContentsMargins(0, 0, 0, 0)
        self.video_layout.setSpacing(0)
        try:
            self.player = MpvVideo(self.video)
            self.video_layout.addWidget(self.player, 1)
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
        self._thread_epg = _CaricaGuide(self.sessione)
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
        view = self.menuBar().addMenu("View")
        view.addAction(self._azione("Fullscreen", self.schermo_intero, "F"))
        help_menu = self.menuBar().addMenu("Help")
        help_menu.addAction(self._azione("About XVB", self.informazioni))




    def _comando(self, *argomenti):
        if self.player:
            self.player.comando(*argomenti)

    def _imposta(self, nome, valore):
        if self.player:
            self.player.imposta(nome, valore)

    def _ciclo(self, nome):
        if self.player:
            self.player.ciclo(nome)

    def _ciclo_valori(self, nome, *valori):
        if self.player:
            self.player.comando("cycle-values", nome, *valori)

    def _regola(self, nome, valore):
        if self.player:
            self.player.regola(nome, valore)

    def _azzera_video(self):
        if self.player:
            for nome in ("brightness", "contrast", "saturation", "gamma", "hue"):
                self.player.imposta(nome, 0)


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
        for lista in precedente.liste:
            if lista["percorso"].startswith(("http://", "https://")):
                continue
            if os.path.isdir(lista["percorso"]):
                nuovi = [(n, p, ide, "Local", lista["percorso"])
                         for n, p, ide in media_in(lista["percorso"])]
                if nuovi:
                    nuova.canali.extend(nuovi)
                    nuova.liste.append(lista)
        self.sessione = nuova
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
        self._thread_epg = _CaricaGuide(self.sessione)
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
        self._canali_visibili = self.sessione.canali_per(percorso, categoria, ricerca)
        for i, voce in enumerate(self._canali_visibili):
            nome, url, ide, gruppo, _lista = voce
            self.elenco.insert("", "end", iid=str(i), text=nome + "\n" + gruppo,
                               colore="#9e9e9e")

    def _seleziona_canale(self):
        selezione = self.elenco.selection()
        if not selezione:
            return
        voce = self._canali_visibili[int(selezione[0])]
        self.riga_stato.setText(voce[0])
        self.apri(voce[1])

    def _apri_selezionato(self, _item=None):
        selezione = self.elenco.selection()
        if selezione:
            voce = self._canali_visibili[int(selezione[0])]
            self.apri(voce[1])


    def apri_cartella(self):
        cartella = QFileDialog.getExistingDirectory(self, "Open folder")
        if not cartella:
            return
        gia = {voce[1] for voce in self.sessione.canali}
        nuovi = [(nome, percorso, ide, "Local", cartella)
                 for nome, percorso, ide in media_in(cartella) if percorso not in gia]
        if not nuovi:
            self.riga_stato.setText("No media files found")
            return
        self.sessione.canali.extend(nuovi)
        self.sessione.liste.append({
            "percorso": cartella, "nome": os.path.basename(cartella),
            "canali": [(n, p, i) for n, p, i, _c, _l in nuovi],
            "categorie": {p: "Local" for _n, p, _i, _c, _l in nuovi},
        })
        self._riempi_liste()
        self._percorso_attivo, self._categoria_attiva = cartella, None
        self._riempi_elenco()
        self.riga_stato.setText("%d media files" % len(nuovi))

    def informazioni(self):
        QMessageBox.about(self, "XVB", "XVB Player 4.4.4")

    def apri_file(self):
        percorso, _ = QFileDialog.getOpenFileName(self, "Open file")
        if percorso:
            self.apri(percorso)

    def apri_url(self):
        url, ok = QInputDialog.getText(self, "Open URL", "URL")
        if ok and url.strip():
            self.apri(url.strip())

    def apri(self, percorso, url=None, ide=None):
        if url is not None:
            percorso = url
        if self.player is None:
            QMessageBox.warning(self, "XVB", "libmpv non disponibile")
            return
        try:
            self.player.apri(percorso)
            self.riga_stato.setText(percorso)
            self.play_button.setText("Ⅱ")
        except Exception as errore:
            QMessageBox.critical(self, "XVB", str(errore))

    def pausa(self):
        if self.player:
            self.player.pausa()
            self.play_button.setText("▶" if self.player.leggi("pause") == "yes" else "Ⅱ")

    def ferma(self):
        if self.player:
            self.player.ferma()
            self.play_button.setText("▶")
            self.riga_stato.setText("XVB")

    def _volume(self, valore):
        if self.player:
            self.player.volume(valore)

    def _seek(self):
        if self.player:
            durata = self.player.leggi("duration")
            if durata:
                self.player.seek(float(durata) * self.posizione.value() / 1000.0)

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
        if self.player:
            self.player.chiudi()
        super().closeEvent(evento)
