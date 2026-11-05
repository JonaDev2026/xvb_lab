from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtCore import QSize
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel,
    QPushButton, QMenuBar, QSizePolicy
)

from core.constants import VERSIONE, FONDO, PANNELLO, BARRA, STATO, TESTO, GRIGIO, ACCENTO
from core.mpv import MpvPlayer
from .widgets import Ricerca, Cursore
from .list import Elenco


class FinestraXVB(QMainWindow):
    comando = Signal(str)

    def __init__(self, controller=None, parent=None, directory=None, mpv_options=None):
        super().__init__(parent)
        self.controller = controller
        self.directory = Path(directory) if directory else Path(__file__).resolve().parents[1]
        self.setWindowTitle("XVB v" + VERSIONE)
        self.resize(1280, 720)
        self.setMinimumSize(760, 420)
        self.setStyleSheet("QMainWindow{background:%s;color:%s}" % (FONDO, TESTO))
        self._azioni = {}
        self._crea_menu()
        self._crea_layout()

    def _crea_menu(self):
        barra = self.menuBar()
        barra.setStyleSheet(
            "QMenuBar{background:%s;color:#ffffff;border:0;padding:3px}"
            "QMenuBar::item{padding:6px 10px;background:transparent}"
            "QMenuBar::item:selected{background:%s}"
            "QMenu{background:%s;color:%s;border:1px solid %s;padding:3px}"
            "QMenu::item{padding:7px 20px}"
            "QMenu::item:selected{background:%s;color:#ffffff}"
            "QMenu::item:disabled{color:%s}" %
            (PANNELLO, ACCENTO, PANNELLO, TESTO, ACCENTO, ACCENTO, GRIGIO))
        self.menu_media = barra.addMenu("Media")
        self.menu_playback = barra.addMenu("Playback")
        self.menu_video = barra.addMenu("Video")
        self.menu_audio = barra.addMenu("Audio")
        self.menu_iptv = barra.addMenu("IPTV")
        self.menu_view = barra.addMenu("View")
        self.menu_help = barra.addMenu("Help")
        self._menu_map = {
            "Media": self.menu_media, "Playback": self.menu_playback,
            "Video": self.menu_video, "Audio": self.menu_audio,
            "IPTV": self.menu_iptv, "View": self.menu_view, "Help": self.menu_help,
        }

    def imposta_menu(self, titolo, voci):
        menu = self._menu_map[titolo]
        menu.clear()
        for voce in voci:
            if voce is None:
                menu.addSeparator()
                continue
            testo, nome_metodo, *resto = voce
            spunta = testo.startswith("*  ")
            if testo[:3] in ("*  ", "   "):
                testo = testo[3:]
            azione = QAction(("✓  " if spunta else "") + testo, self)
            metodo = getattr(self.controller, nome_metodo, None) if self.controller else None
            azione.setEnabled(callable(metodo))
            if callable(metodo):
                azione.triggered.connect(metodo)
            menu.addAction(azione)

    def _crea_layout(self):
        centro = QWidget(self)
        self.setCentralWidget(centro)
        principale = QHBoxLayout(centro)
        principale.setContentsMargins(0, 0, 0, 0)
        principale.setSpacing(0)

        self.sinistra = QFrame(centro)
        self.sinistra.setFixedWidth(300)
        self.sinistra.setStyleSheet("background:%s" % PANNELLO)
        sx = QVBoxLayout(self.sinistra)
        sx.setContentsMargins(10, 10, 10, 8)
        sx.setSpacing(8)
        self.cerca = Ricerca(self.sinistra, self._filtra, vuota="Search")
        sx.addWidget(self.cerca)
        self.elenco = Elenco(self.sinistra)
        self.elenco.segno = "logo"
        sx.addWidget(self.elenco, 1)
        principale.addWidget(self.sinistra)

        self.video_area = QWidget(centro)
        self.video_area.setStyleSheet("background:#000000")
        video_layout = QVBoxLayout(self.video_area)
        video_layout.setContentsMargins(0, 0, 0, 0)
        video_layout.setSpacing(0)
        self.video = MpvPlayer(self.video_area, options=mpv_options)
        for proprieta in ("time-pos", "duration", "pause", "volume", "mute", "media-title", "playlist-pos", "speed"):
            self.video.osserva(proprieta)
        self.video.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        video_layout.addWidget(self.video, 1)
        self.barra = QFrame(self.video_area)
        self.barra.setFixedHeight(96)
        self.barra.setStyleSheet("background:%s" % BARRA)
        comandi = QVBoxLayout(self.barra)
        comandi.setContentsMargins(12, 5, 12, 5)
        comandi.setSpacing(5)
        self.seek = QSlider(Qt.Horizontal, self.barra)
        self.seek.setRange(0, 100)
        self.seek.setFixedHeight(10)
        self.seek.setStyleSheet("QSlider::groove:horizontal{height:2px;background:#4a4a4a}QSlider::sub-page:horizontal{background:#ffffff}QSlider::handle:horizontal{width:0;background:transparent;border:0}")
        self.seek.sliderMoved.connect(self._seek)
        comandi.addWidget(self.seek)
        riga = QHBoxLayout()
        riga.setSpacing(8)
        self.pulsanti = {}
        controlli = (
            ("prima", "Previous", "skip_previous"),
            ("-10", "Back 10 s", None),
            ("play", "Play / Pause", "play"),
            ("stop", "Stop", "stop"),
            ("+10", "Forward 10 s", None),
            ("dopo", "Next", "skip_next"),
            ("rec", "Record", "radio_button_checked"),
            ("repeat", "Repeat", "repeat"),
            ("shuffle", "Shuffle", "shuffle"),
        )
        for chiave, etichetta, icona in controlli:
            b = QPushButton(self.barra)
            b.setToolTip(etichetta)
            percorso = self.directory / "icone" / (chiave + ".png")
            if percorso.is_file():
                b.setIcon(QIcon(str(percorso)))
                lato = 34 if chiave in ("prima", "dopo", "play") else 24
                b.setIconSize(QSize(lato, lato))
                b.setFixedSize(lato + 12, lato + 12)
            else:
                b.setText(etichetta)
            b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet(
                "QPushButton{background:transparent;color:%s;border:0;padding:3px}"
                "QPushButton:hover{background:%s}" % (TESTO, ACCENTO))
            b.clicked.connect(lambda _v=False, k=chiave: self._azione(k))
            self.pulsanti[chiave] = b
            riga.addWidget(b)
        riga.addStretch(1)
        for chiave, etichetta in (
            ("favorite_off", "Favorite"), ("pip", "Picture in picture"),
            ("pieno", "Fullscreen"), ("setting", "Quality"),
            ("playlist", "Playlists"), ("volume", "Mute")
        ):
            b = QPushButton(self.barra)
            b.setToolTip(etichetta)
            percorso = self.directory / "icone" / (chiave + ".png")
            if percorso.is_file():
                b.setIcon(QIcon(str(percorso)))
                b.setIconSize(QSize(24, 24))
                b.setFixedSize(32, 32)
            else:
                b.setText(etichetta)
            b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet(
                "QPushButton{background:transparent;color:%s;border:0;padding:3px}"
                "QPushButton:hover{background:%s}" % (TESTO, ACCENTO))
            b.clicked.connect(lambda _v=False, k=chiave: self._azione(k))
            self.pulsanti[chiave] = b
            riga.addWidget(b)
        comandi.addLayout(riga)
        self.volume = Cursore(self.barra, self._volume, larga=85, alta=26)
        self.volume.setFixedWidth(85)
        riga.addWidget(self.volume)
        video_layout.addWidget(self.barra)
        principale.addWidget(self.video_area, 1)

        self.destra = QFrame(centro)
        self.destra.setFixedWidth(220)
        self.destra.setStyleSheet("background:%s" % PANNELLO)
        dx = QVBoxLayout(self.destra)
        dx.setContentsMargins(10, 10, 10, 8)
        dx.setSpacing(8)
        self.et_liste = QLabel("Playlists", self.destra)
        self.et_liste.setStyleSheet("color:%s" % GRIGIO)
        dx.addWidget(self.et_liste)
        self.pannello_destro = QWidget(self.destra)
        dx.addWidget(self.pannello_destro, 1)
        principale.addWidget(self.destra)

        self.stato = QLabel("ready", self)
        self.stato.setFixedHeight(28)
        self.stato.setContentsMargins(10, 0, 10, 0)
        self.stato.setStyleSheet("background:%s;color:%s" % (STATO, GRIGIO))
        self.statusBar().addWidget(self.stato, 1)
        self.statusBar().setFixedHeight(28)
        self.statusBar().setStyleSheet("QStatusBar{background:%s;border:0}" % STATO)

    def _azione(self, chiave):
        if self.controller:
            mappa = {
                "prima": ("salta", -1), "dopo": ("salta", 1),
                "-10": ("avanza", -10), "+10": ("avanza", 10),
                "play": ("pausa", None), "stop": ("ferma", None),
                "rec": ("registra", None), "repeat": ("gira_ripeti", None),
                "shuffle": ("shuffle", None), "favorite_off": ("preferito", None),
                "pieno": ("schermo_intero", None), "pip": ("pip_si_no", None),
                "setting": ("apri_menu_qualita", None),
                "playlist": ("sidebar", None), "volume": ("muto", None),
            }
            nome, argomento = mappa.get(chiave, (chiave, None))
            metodo = getattr(self.controller, nome, None)
            if callable(metodo):
                metodo(argomento) if argomento is not None else metodo()
        self.comando.emit(chiave)

    def _filtra(self):
        if self.controller:
            metodo = getattr(self.controller, "filtra", None)
            if callable(metodo):
                metodo()

    def _seek(self, valore):
        if self.controller:
            metodo = getattr(self.controller, "seek_percentuale", None)
            if callable(metodo):
                metodo(valore)

    def _volume(self, valore):
        if self.controller:
            metodo = getattr(self.controller, "alza_volume", None)
            if callable(metodo):
                metodo(valore)

    def imposta_stato(self, testo):
        self.stato.setText(testo)

    def imposta_pannello_destro(self, widget):
        layout = self.destra.layout()
        layout.replaceWidget(self.pannello_destro, widget)
        self.pannello_destro.deleteLater()
        self.pannello_destro = widget

    def chiudi(self):
        self.video.chiudi()
        self.close()

    def closeEvent(self, evento):
        self.video.chiudi()
        super().closeEvent(evento)
