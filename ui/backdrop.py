import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import QWidget

from core.constants import QUI


class Sfondo(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._predefinita = os.path.join(QUI, "icone", "screen.png")
        self._percorso = None
        self._pixmap = QPixmap()
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background:#000000")

    def imposta(self, immagine=None):
        percorso = immagine if isinstance(immagine, str) else None
        if percorso is None:
            self._percorso = None
            nuovo = QPixmap(self._predefinita)
        elif percorso == self._percorso:
            return
        else:
            self._percorso = percorso
            nuovo = QPixmap(percorso)
        if nuovo.isNull():
            nuovo = QPixmap(self._predefinita)
        self._pixmap = nuovo
        self.update()

    def imposta_pixmap(self, immagine):
        if isinstance(immagine, QPixmap):
            self._pixmap = immagine
        else:
            self._pixmap = QPixmap()
        if self._pixmap.isNull():
            self._pixmap = QPixmap(self._predefinita)
        self._percorso = None
        self.update()

    def paintEvent(self, evento):
        pittore = QPainter(self)
        pittore.fillRect(self.rect(), QColor("#000000"))
        if not self._pixmap.isNull():
            immagine = self._pixmap.scaled(
                self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            x = (self.width() - immagine.width()) // 2
            y = (self.height() - immagine.height()) // 2
            pittore.drawPixmap(x, y, immagine)
        pittore.end()
