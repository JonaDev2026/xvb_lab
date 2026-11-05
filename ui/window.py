from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QIcon
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

    def __init__(self, controller=None, parent=None, directory=None):
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
        self.video = MpvPlayer(self.video_area)
        self.video.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        video_layout.addWidget(self.video, 1)
        self.barra = QFrame(self.video_area)
        self.barra.setFixedHeight(96)
        self.barra.setStyleSheet("background:%s" % BARRA)
        comandi = QVBoxLayout(self.barra)
        comandi.setContentsMargins(12, 5, 12, 5)
        comandi.setSpacing(5)
        riga = QHBoxLayout()
        riga.setSpacing(8)
        self.pulsanti = {}
        for chiave, etichetta in (
            ("prima", "Previous"), ("play", "Play"), ("stop", "Stop"),
            ("dopo", "Next"), ("volume", "Volume")
        ):
            b = QPushButton(etichetta, self.barra)
            b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet(
                "QPushButton{background:transparent;color:%s;border:0;padding:6px}"
                "QPushButton:hover{color:%s}" % (TESTO, ACCENTO))
            b.clicked.connect(lambda _v=False, k=chiave: self._azione(k))
            self.pulsanti[chiave] = b
            riga.addWidget(b)
        riga.addStretch(1)
        comandi.addLayout(riga)
        self.cursore = Cursore(self.barra, self._seek, larga=170, alta=26)
        comandi.addWidget(self.cursore)
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
            metodo = getattr(self.controller, chiave, None)
            if callable(metodo):
                metodo()
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
