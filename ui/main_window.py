from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QAction, QKeySequence, QIcon
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFileDialog, QInputDialog, QMessageBox, QSlider
)
from engine.mpv import MpvVideo
from ui.widgets import Elenco


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
        self.elenco = Elenco(self.sinistra)
        sx.addWidget(self.elenco, 1)

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
        dx.addWidget(QLabel("XVB", self.destra))
        dx.addStretch(1)

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

    def _azione(self, nome, callback, scorciatoia=None):
        azione = QAction(nome, self)
        if scorciatoia:
            azione.setShortcut(QKeySequence(scorciatoia))
        azione.triggered.connect(callback)
        return azione

    def _costruisci_menu(self):
        media = self.menuBar().addMenu("Media")
        media.addAction(self._azione("Open file...", self.apri_file, "Ctrl+O"))
        media.addAction(self._azione("Open URL...", self.apri_url, "Ctrl+L"))
        media.addSeparator()
        media.addAction(self._azione("Quit", self.close, "Ctrl+Q"))
        playback = self.menuBar().addMenu("Playback")
        playback.addAction(self._azione("Play / Pause", self.pausa, "Space"))
        playback.addAction(self._azione("Stop", self.ferma, "S"))
        view = self.menuBar().addMenu("View")
        view.addAction(self._azione("Fullscreen", self.schermo_intero, "F"))

    def apri_file(self):
        percorso, _ = QFileDialog.getOpenFileName(self, "Open file")
        if percorso:
            self.apri(percorso)

    def apri_url(self):
        url, ok = QInputDialog.getText(self, "Open URL", "URL")
        if ok and url.strip():
            self.apri(url.strip())

    def apri(self, percorso):
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
